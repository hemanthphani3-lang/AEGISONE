package main

import (
	"context"
	"fmt"
	"io"
	"log"
	"net/http"
	"net/http/httputil"
	"net/url"
	"os"
	"os/exec"
	"os/signal"
	"sync/atomic"
	"syscall"
	"time"
)

var (
	keycloakReady atomic.Bool
	targetURL     *url.URL
	reverseProxy  *httputil.ReverseProxy
)

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	internalPort := "8081" // Keycloak listens internally on 127.0.0.1:8081

	var err error
	targetURL, err = url.Parse(fmt.Sprintf("http://127.0.0.1:%s", internalPort))
	if err != nil {
		log.Fatalf("[Proxy] Failed to parse target URL: %v", err)
	}

	reverseProxy = httputil.NewSingleHostReverseProxy(targetURL)

	// Director preserves incoming host headers and proxy headers
	originalDirector := reverseProxy.Director
	reverseProxy.Director = func(req *http.Request) {
		originalDirector(req)
		req.Header.Set("X-Forwarded-Host", req.Host)
		if req.TLS != nil {
			req.Header.Set("X-Forwarded-Proto", "https")
		} else if proto := req.Header.Get("X-Forwarded-Proto"); proto != "" {
			req.Header.Set("X-Forwarded-Proto", proto)
		} else {
			req.Header.Set("X-Forwarded-Proto", "http")
		}
	}

	// 1. Immediately bind HTTP listener on 0.0.0.0:$PORT
	server := &http.Server{
		Addr:    ":" + port,
		Handler: http.HandlerFunc(handleRequest),
	}

	listenerStarted := make(chan struct{})
	go func() {
		log.Printf("[Proxy] Binding HTTP listener on 0.0.0.0:%s...", port)
		close(listenerStarted)
		if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
			log.Fatalf("[Proxy] HTTP listener error: %v", err)
		}
	}()

	<-listenerStarted
	time.Sleep(50 * time.Millisecond)
	log.Printf("[Proxy] HTTP listener is OPEN on 0.0.0.0:%s for Render port detection.", port)

	// 2. Launch internal Keycloak process on 127.0.0.1:8081
	kcCmd := exec.Command("/opt/keycloak/bin/kc.sh", "start", "--optimized", "--import-realm",
		"--http-host=127.0.0.1", fmt.Sprintf("--http-port=%s", internalPort))
	kcCmd.Stdout = os.Stdout
	kcCmd.Stderr = os.Stderr
	kcCmd.Env = os.Environ()

	log.Printf("[Proxy] Launching internal Keycloak process on 127.0.0.1:%s...", internalPort)
	if err := kcCmd.Start(); err != nil {
		log.Fatalf("[Proxy] Failed to start Keycloak process: %v", err)
	}

	// 3. Monitor Keycloak readiness in background
	go monitorKeycloakHealth(internalPort)

	// 4. Handle Signals and Process Supervision
	sigChan := make(chan os.Signal, 1)
	signal.Notify(sigChan, syscall.SIGTERM, syscall.SIGINT)

	kcExitChan := make(chan error, 1)
	go func() {
		kcExitChan <- kcCmd.Wait()
	}()

	select {
	case sig := <-sigChan:
		log.Printf("[Proxy] Received signal %v, shutting down Keycloak gracefully...", sig)
		if kcCmd.Process != nil {
			_ = kcCmd.Process.Signal(syscall.SIGTERM)
		}
		select {
		case <-kcExitChan:
			log.Printf("[Proxy] Keycloak process terminated cleanly.")
		case <-time.After(10 * time.Second):
			log.Printf("[Proxy] Keycloak shutdown timed out, killing process...")
			_ = kcCmd.Process.Kill()
		}
		ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)

	case err := <-kcExitChan:
		if err != nil {
			log.Printf("[Proxy] Keycloak process exited with error: %v", err)
		} else {
			log.Printf("[Proxy] Keycloak process exited cleanly.")
		}
		ctx, cancel := context.WithTimeout(context.Background(), 2*time.Second)
		defer cancel()
		_ = server.Shutdown(ctx)
		os.Exit(1)
	}
}

func monitorKeycloakHealth(internalPort string) {
	healthURL := fmt.Sprintf("http://127.0.0.1:%s/health/ready", internalPort)
	client := &http.Client{Timeout: 2 * time.Second}

	for {
		resp, err := client.Get(healthURL)
		if err == nil && resp.StatusCode == http.StatusOK {
			_, _ = io.Copy(io.Discard, resp.Body)
			resp.Body.Close()
			if !keycloakReady.Load() {
				keycloakReady.Store(true)
				log.Printf("[Proxy] Keycloak is READY on 127.0.0.1:%s! Proxying all traffic.", internalPort)
			}
		} else {
			if resp != nil {
				resp.Body.Close()
			}
			if keycloakReady.Load() {
				keycloakReady.Store(false)
				log.Printf("[Proxy] Keycloak readiness probe lost.")
			}
		}
		time.Sleep(1 * time.Second)
	}
}

func handleRequest(w http.ResponseWriter, r *http.Request) {
	if keycloakReady.Load() {
		reverseProxy.ServeHTTP(w, r)
		return
	}

	// Early HTTP response before Keycloak becomes ready (so Render port scan succeeds immediately)
	if r.URL.Path == "/" || r.URL.Path == "/health" || r.URL.Path == "/health/ready" || r.URL.Path == "/health/live" {
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"status":"INITIALIZING","message":"Keycloak server is warming up and initializing database schema..."}`))
		return
	}

	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Retry-After", "5")
	w.WriteHeader(http.StatusServiceUnavailable)
	_, _ = w.Write([]byte(`{"error":"service_unavailable","message":"Keycloak is currently initializing. Please retry in a few seconds."}`))
}
