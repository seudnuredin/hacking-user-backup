package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/url"
	"os"

	wappalyzer "github.com/projectdiscovery/wappalyzergo"
)

func main() {
	// Parse the URL and proxy from command line arguments
	targetURL := flag.String("url", "", "URL to scan with Wappalyzer")
	proxyURL := flag.String("proxy", "", "Proxy URL to use for the request (e.g., http://proxy:port)")
	flag.Parse()

	// Check if URL is provided
	if *targetURL == "" {
		fmt.Println("Usage: go run wappalyzer.go -url=<target_url> [-proxy=<proxy_url>]")
		os.Exit(1)
	}

	// Create a custom HTTP transport if a proxy is provided
	var client *http.Client
	if *proxyURL != "" {
		proxy, err := url.Parse(*proxyURL)
		if err != nil {
			log.Fatal("Invalid proxy URL:", err)
		}
		transport := &http.Transport{
			Proxy: http.ProxyURL(proxy),
		}
		client = &http.Client{Transport: transport}
	} else {
		client = http.DefaultClient
	}

	// Make HTTP request to the provided URL
	resp, err := client.Get(*targetURL)
	if err != nil {
		log.Fatal(err)
	}
	defer resp.Body.Close() // Ensure the response body is closed

	// Read response body
	data, err := io.ReadAll(resp.Body)
	if err != nil {
		log.Fatal(err)
	}

	// Initialize Wappalyzer and fingerprint the technologies
	wappalyzerClient, err := wappalyzer.New()
	if err != nil {
		log.Fatal(err)
	}
	fingerprints := wappalyzerClient.Fingerprint(resp.Header, data)

	// Convert the output to JSON format
	jsonOutput, err := json.MarshalIndent(fingerprints, "", "  ")
	if err != nil {
		log.Fatal(err)
	}

	// Print the JSON output
	fmt.Println(string(jsonOutput))
}
