/* **********************************************************
 * Copyright (c) 2011 Google, Inc.  All rights reserved.
 * **********************************************************/

/*
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * * Redistributions of source code must retain the above copyright notice,
 *   this list of conditions and the following disclaimer.
 *
 * * Redistributions in binary form must reproduce the above copyright notice,
 *   this list of conditions and the following disclaimer in the documentation
 *   and/or other materials provided with the distribution.
 *
 * * Neither the name of Google, Inc. nor the names of its contributors may be
 *   used to endorse or promote products derived from this software without
 *   specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL GOOGLE, INC. OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
 * OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
 * DAMAGE.
 */

// Wraps (hijacks) interesting OpenSSL functions using DynamoRIO
// Copyright (c) Dhiru Kholia (dhiru [at] openwall [dot] com)
//
// Usage:
//
// bin64/drrun -v -c samples/bin/libwrap.so -- ~/.dropbox-dist/dropbox

#include "dr_api.h"
#include "drwrap.h"

static void *lock;

static void event_exit(void);
static void wrap_pre_write(void *wrapcxt, OUT void **user_data);
static void wrap_pre_read(void *wrapcxt, OUT void **user_data);
static void wrap_post(void *wrapcxt, void *user_data);

unsigned char *read_bufer = NULL;
int read_bufer_len =0;

static
void module_load_event(void *drcontext, const module_data_t * mod, bool loaded)
{
	app_pc towrap = (app_pc)
	    dr_get_proc_address(mod->handle, "SSL_write");
	if (towrap != NULL) {
		bool ok = drwrap_wrap(towrap, wrap_pre_write, NULL);
		if (!ok) {
			printf("WTF?\n");
			drwrap_exit();
		}
	}

	app_pc towrap2 = (app_pc)
	    dr_get_proc_address(mod->handle, "SSL_read");
	if (towrap2 != NULL) {
		bool ok = drwrap_wrap(towrap2, wrap_pre_read, wrap_post);
		if (!ok) {
			printf("WTF?\n");
			drwrap_exit();
		}
	}
}

DR_EXPORT void dr_init(client_id_t id)
{
	/* make it easy to tell, by looking at log file, which client executed */
	dr_log(NULL, LOG_ALL, 1, "Client 'wrap' initializing\n");
#ifdef SHOW_RESULTS
	if (dr_is_notify_on()) {
#ifdef WINDOWS
		dr_enable_console_printing();
#endif
		dr_fprintf(STDERR, "Client wrap is running\n");
	}
#endif
	drwrap_init();
	dr_register_module_load_event(module_load_event);
	lock = dr_mutex_create();
}

static void wrap_pre_write(void *wrapcxt, OUT void **user_data)
{
	// http://www.openssl.org/docs/ssl/SSL_write.html
	// int SSL_write(SSL *ssl, const void *buf, int num);
	unsigned char *buf = (unsigned char *) drwrap_get_arg(wrapcxt, 1);
	puts(buf);
	size_t sz = (size_t) drwrap_get_arg(wrapcxt, 2);
	printf("\n<<< Write Size is %d >>>\n", sz);
}

static void wrap_pre_read(void *wrapcxt, OUT void **user_data)
{
	dr_mutex_lock(lock);
	// int SSL_read(SSL *ssl, void *buf, int num);
	read_bufer = (unsigned char *) drwrap_get_arg(wrapcxt, 1);
	read_bufer_len = (size_t) drwrap_get_arg(wrapcxt, 2);
}

static void wrap_post(void *wrapcxt, void *user_data)
{
	dr_mutex_unlock(lock);
	if (read_bufer_len < 8) {
		// short messages are not interesting
		return;
	}
	puts(read_bufer);
	printf("\n<<< Read Size is %d >>>\n", read_bufer_len);
}
