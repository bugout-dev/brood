/*
Brood API middlewares.
*/
package cmd

import (
	"fmt"
	"net/http"
	"strings"
	"time"
)

// Handle panic errors to prevent server shutdown
func panicMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		defer func() {
			if err := recover(); err != nil {
				fmt.Println("recovered", err)
				http.Error(w, "Internal server error", 500)
			}
		}()

		// There will be a defer with panic handler in each next function
		next.ServeHTTP(w, r)
	})
}

// Log access requests in proper format
func logMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		start := time.Now()
		next.ServeHTTP(w, r)
		fmt.Printf("[%s] %s %s %s\n", time.Since(start), r.Method, r.URL.Path, r.RemoteAddr)
	})
}

// CORS middleware
func corsMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// fmt.Println("corsMiddleware", r.URL.Path)
		next.ServeHTTP(w, r)
	})
}

// Authorization Bearer header check
func authMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Extract authorization headers
		// And reject access if more then 10 authorization headers provided
		authHeaders := r.Header["Authorization"]
		authHeadersLen := len(authHeaders)
		if authHeadersLen == 0 {
			http.Error(w, "Authorization header not found", http.StatusBadRequest)
			return
		}
		if authHeadersLen >= 10 {
			http.Error(w, "Unacceptable headers provided", http.StatusBadRequest)
			return
		}

		// Extract Bearer tokens
		bearerTokens := make([]string, 0, 10)
		for _, h := range authHeaders {
			hList := strings.Split(h, " ")
			if len(hList) != 2 {
				http.Error(w, "Unacceptable token format provided", http.StatusBadRequest)
				return
			}
			if hList[0] == "Bearer" {
				bearerTokens = append(bearerTokens, hList[1])
			}
		}

		if len(bearerTokens) == 0 {
			http.Error(w, "Unacceptable token format provided", http.StatusBadRequest)
			return
		}

		// Check there is active token
		isActive := false
		for _, t := range bearerTokens {
			// TODO(kompotkot): Request to database
			if t == "678d0954-371c-48a6-a7ec-6d7abecd094d" {
				isActive = true
			}
		}
		if isActive == false {
			http.Error(w, "Invalid token", http.StatusUnauthorized)
			return
		}

		next.ServeHTTP(w, r)
	})
}

