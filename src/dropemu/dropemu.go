package main

import (
	"bytes"
	"crypto/tls"
	// "encoding/base64"
	"encoding/hex"
	// "encoding/pem"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/google/uuid"
	"io/ioutil"
	// "math/big"
	"net/http"
	"net/url"
	// "net/url"
	"bufio"
	"compress/zlib"
	"io"
	"os"
	"strconv"
	"strings"
	"time"
	// "path/filepath"
	// "strings"
	// "text/template"
)

// Dropbox URLs
var nonceURL string = "https://client-lb.dropbox.com/cli_link_nonce_gen"
var registerURL string = "https://client.dropbox.com/register_host"
var listURL string = "https://client-cf.dropbox.com/list"
var fetchURL string = "https://block.dropbox.com/retrieve_batch"
var commitURL string = "https://client-cf.dropbox.com/commit_batch"
var storeURL string = "https://block.dropbox.com/store_batch"

// https://matt.aimonetti.net/posts/2013/07/01/golang-multipart-file-upload-example/

// "constant" data
var un string = `["Linux", "localhost.localdomain", "4.12.9-200.fc25.x86_64", "#1 SMP Fri Aug 25 13:23:30 UTC 2017", "x86_64", "x86_64"]`
var buildno string = "Dropbox-lnx.x86_64-34.4.22"

// global
var root_ns string
var host_key string

// templates
const registerTemplate = `nonce=None&host_characteristics={}&sscv_auth_version=2&machine_id=00000000-0000-0000-0000-000000000000&sync_engine_version=33.4.16&uuid=%s&server_list=True&install_type=None&hostname=localhost.localdomain&update_manager_id=None&host_key=%s&client_info={}&platform_version=None&buildno=%s&un=%s&cdm_version=6&tag=`

const listTemlate = `host_key=%s&initial_list=1&server_list=1&use_64bit_ns_ids=True&home_ns_id=%s&need_sandboxes=1&home_ns_path=&include_deleted=1&extended_namespace_info=1&buildno=%s&ns_p2p_key_map={"%s": null}&cdm_version=6&paired_host_key=None&dict_return=1&root_ns_id=%s&ns_cursors=%s:&return_file_ids=1&xattrs=1&only_directories=0`

const fetchTemplate = ``

type register_host struct {
	HostInt         int64  `json:"host_int"`
	ServerTime      int    `json:"server_time"`
	HostKey         string `json:"host_key"`
	RootNS          *int   `json:"root_ns"`
	HostID          string `json:"host_id"`
	UserDisplayName string `json:"userdisplayname"`
	Email           string `json:"email"`
}

type cli_link_nonce_gen struct {
	NonceURI string `json:"nonce_uri"`
}

type list struct {
	HostInt int64 `json:"host_int"`
	List    []struct {
		Attrs struct {
		} `json:"attrs"`
		Mtime     int    `json:"mtime"`
		Path      string `json:"path"`
		IsDir     bool   `json:"is_dir"`
		Size      int    `json:"size"`
		UserID    int    `json:"user_id"`
		FileidGid string `json:"fileid_gid"`
		Blocklist string `json:"blocklist"`
		Ts        int    `json:"ts"`
		IID       int
	} `json:"list"`
}

var db list

// Prepare a request handler with suitable headers
func requestPrepare(url string, data string) (*http.Request, error) {
	req, err := http.NewRequest("POST", url, bytes.NewBufferString(data))
	req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	UUID := [16]byte(uuid.New())
	req.Header["X-DBX-REQ-ID"] = []string{hex.EncodeToString(UUID[:])}
	req.Header["X-Dropbox-User-Agent"] = []string{"DropboxDesktopClient/34.4.22 (Linux; 4.12.9-200.fc25.x86_64; x64; en_US)"}
	req.Header["User-Agent"] = []string{"DropboxDesktopClient/34.4.22 (Linux; 4.12.9-200.fc25.x86_64; x64; en_US)"}
	req.Header["X-DBX-RETRY"] = []string{"1"}
	req.Header["X-Dropbox-Locale"] = []string{"en_US"}

	return req, err
}

func link_device() error {
	registerData := fmt.Sprintf(registerTemplate, "", "None", buildno, un)
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		Proxy:           http.ProxyFromEnvironment,
	}
	client := &http.Client{Transport: tr}

	// Get a host_id / host_key assigned
	req, err := requestPrepare(registerURL, registerData)
	if err != nil {
		panic(err)
	}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	var r register_host
	err = json.Unmarshal(body, &r)
	if r.HostKey == "" {
		panic("Failed in getting host_key assigned, dumping response below\n\n" + string(body))
	}
	fmt.Printf("Your host_id / host_key / host_secret is %s.\n\n", r.HostKey)

	// Link this host_key with the Dropbox account
	data := fmt.Sprintf("host_key=%s&cli_nonce=None", r.HostKey)
	req, err = requestPrepare(nonceURL, data)
	if err != nil {
		panic(err)
	}
	resp, err = client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err = ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	var rn cli_link_nonce_gen
	err = json.Unmarshal(body, &rn)
	if rn.NonceURI == "" {
		panic("Failed in getting nonce_uri for registration, dumping response below\n\n" + string(body))
	}

	fmt.Printf("Please visit %s in a web browser to link this device.\n\n", rn.NonceURI)
	// Check if this device has been linked so far!
	registerData = fmt.Sprintf(registerTemplate, "", r.HostKey, buildno, un)
	for {
		time.Sleep(time.Second * 8)

		req, err = requestPrepare(registerURL, registerData)
		if err != nil {
			panic(err)
		}
		resp, err = client.Do(req)
		if err != nil {
			panic(err)
		}
		defer resp.Body.Close()
		body, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			panic(err)
		}
		err = json.Unmarshal(body, &r)
		if r.RootNS != nil {
			break
		}
	}

	fmt.Printf("Your host_id / host_key / host_secret is %s.\n\n", r.HostKey)
	fmt.Printf("The associated email address is %s and user name is %s.\n", r.Email, r.UserDisplayName)

	return nil
}

func do_ls() error {
	payload := fmt.Sprintf(listTemlate, host_key, root_ns, buildno, root_ns, root_ns, root_ns)
	fmt.Println(payload)
	time.Sleep(time.Second * 32)

	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		Proxy:           http.ProxyFromEnvironment,
	}
	client := &http.Client{Transport: tr}
	req, err := requestPrepare(listURL, payload)
	// add extra headers
	req.Header["X-Dropbox-UID"] = []string{"5432112345"} // XXX
	req.Header["X-Dropbox-NSID"] = []string{"all"}
	req.Header["X-Dropbox-Path-Root"] = []string{root_ns}
	if err != nil {
		panic(err)
	}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	err = json.Unmarshal(body, &db)
	if err != nil {
		panic(err)
	}
	iid := 0
	for i, _ := range db.List {
		db.List[i].IID = iid
		iid++
	}
	fmt.Printf("%5s %5s %10s %s\n", "ID", "type", "size", "path")
	for i, _ := range db.List {
		v := db.List[i]
		nature := ""
		if v.IsDir {
			nature = "d"
		} else {
			nature = "f"
		}
		fmt.Printf("%5d %5s %10d %s\n", v.IID, nature, v.Size, v.Path)
	}

	return nil
}

func do_get(iid string) error {
	const fetchTemlate = `host_id=%s&hashes=%s`
	const hashesTemplate = `[["%s", null, null]]`
	target := -1
	type fetchData struct {
		Hash string `json:"hash"`
		Len  int    `json:"len"`
	}

	for i, _ := range db.List {
		v := db.List[i]
		fmt.Println(v)
		fmt.Println(iid)
		if iid == strconv.Itoa(v.IID) {
			target = v.IID
			fmt.Println("XXXXXXXXXXXXXX")
		}
	}

	hashes := fmt.Sprintf(hashesTemplate, db.List[target].Blocklist)
	hashes = url.QueryEscape(hashes)
	payload := fmt.Sprintf(fetchTemlate, host_key, hashes)
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		Proxy:           http.ProxyFromEnvironment,
	}
	client := &http.Client{Transport: tr}
	req, err := requestPrepare(fetchURL, payload)
	// add extra headers
	req.Header["X-Dropbox-UID"] = []string{"5432112345"} // XXX
	req.Header["X-Dropbox-NSID"] = []string{"all"}
	req.Header["X-Dropbox-Path-Root"] = []string{root_ns}
	if err != nil {
		panic(err)
	}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	buffer := bytes.NewBuffer(body)
	// we only handle download for one file at one go
	head, err := buffer.ReadBytes('\n')
	if err != nil {
	}
	chead := bytes.TrimRight(head, "\n")
	var r fetchData
	err = json.Unmarshal(chead, &r)
	compressedData := buffer.Next(r.Len)
	b := bytes.NewReader(compressedData)
	rs, err := zlib.NewReader(b)
	if err != nil {
		panic(err)
	}
	io.Copy(os.Stdout, rs)

	return nil
}

func interactive_shell(host_key string) error {
	scanner := bufio.NewScanner(os.Stdin)

	for {
		fmt.Print("(Cmd) ")
		scanner.Scan()
		line := scanner.Text()

		if strings.Compare("help", line) == 0 {
			fmt.Println("Commands: get | hash | help | lls | ls | put | rm")
		}

		if strings.HasPrefix(line, "ls") {
			login_dropbox(host_key)
			do_ls()
		}

		if strings.HasPrefix(line, "get") {
			login_dropbox(host_key)
			do_ls()
			fields := strings.Split(line, " ")
			fmt.Println(fields)
			do_get(fields[1])
		}

		if err := scanner.Err(); err != nil {
			fmt.Fprintln(os.Stderr, "error:", err)
			os.Exit(1)
		}

		if strings.Compare("", line) == 0 {
			fmt.Println("")
			os.Exit(1)
		}
	}

	return nil
}

func login_dropbox(host_key_local string) error {
	registerData := fmt.Sprintf(registerTemplate, "", host_key_local, buildno, un)
	tr := &http.Transport{
		TLSClientConfig: &tls.Config{InsecureSkipVerify: true},
		Proxy:           http.ProxyFromEnvironment,
	}
	client := &http.Client{Transport: tr}

	req, err := requestPrepare(registerURL, registerData)
	if err != nil {
		panic(err)
	}
	resp, err := client.Do(req)
	if err != nil {
		panic(err)
	}
	defer resp.Body.Close()
	body, err := ioutil.ReadAll(resp.Body)
	if err != nil {
		panic(err)
	}
	var r register_host
	err = json.Unmarshal(body, &r)

	fmt.Printf("Your host_id / host_key / host_secret is %s.\n\n", r.HostKey)
	fmt.Printf("The associated email address is %s and user name is %s.\n", r.Email, r.UserDisplayName)

	root_ns = fmt.Sprintf("%d", *r.RootNS)
	host_key = r.HostKey
	fmt.Println(host_key)

	return nil
}

// AppVersion specifies the current bardemu version
const AppVersion = "bardemu 0.92"

func main() {
	var host_key string
	var interactive bool
	var login bool
	var authorize bool
	var decrypt bool
	var version bool
	var initialize bool

	flag.Usage = func() {
		fmt.Printf("Usage: %s [options]\n", os.Args[0])
		flag.PrintDefaults()
		fmt.Printf("\nTop level actions are -d (decrypt), -l (login + device authorize), -a (book playback authorize), -i (initialize device)\n")
	}

	flag.BoolVar(&login, "l", false, "Login to Dropbox")
	flag.BoolVar(&interactive, "i", false, "Launch Dropbox interactive shell")
	flag.BoolVar(&authorize, "a", false, "Link / authorize the device")
	flag.StringVar(&host_key, "h", "", "Dropbox registered host_key")
	flag.BoolVar(&version, "v", false, "Show bardemu version")
	flag.Parse()

	if version {
		fmt.Println(AppVersion)
		os.Exit(0)
	}

	if !login && !authorize && !decrypt && !initialize && !interactive {
		fmt.Printf("Run '%s -h' for help\n", os.Args[0])
		os.Exit(-1)
	}

	if login {
		if host_key == "" {
			fmt.Println("Dropbox registered host_key is required for login.")
			os.Exit(-2)
		}
		login_dropbox(host_key)
		os.Exit(0)
	}

	if authorize {
		link_device()
		os.Exit(0)
	}

	if interactive {
		if host_key == "" {
			fmt.Println("Dropbox registered host_key is required for the interactive shell.")
			os.Exit(-2)
		}

		interactive_shell(host_key)
		os.Exit(0)
	}
}
