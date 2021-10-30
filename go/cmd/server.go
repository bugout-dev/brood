/*
Brood server API entry point.
*/
package cmd

import (
	"flag"
	"log"
	"net/http"
	"time"

	routes "github.com/bugout-dev/brood/go/cmd/routes"
	brood "github.com/bugout-dev/brood/go/pkg"
)

// Brood server initialization
func InitServer() {
	var listeningAddr string
	var listeningPort string
	flag.StringVar(&listeningAddr, "host", "127.0.0.1", "Server listening address")
	flag.StringVar(&listeningPort, "port", "7474", "Server listening port")
	flag.Parse()

	// Initialize database connection
	sessionDB := brood.InitSessionDB()

	// Set auth middleware
	// authHandler := authMiddleware(authMux)

	userMux := http.NewServeMux()
	userServer := routes.NewUserServer(sessionDB)
	userMux.HandleFunc("/user/", userServer.UserHandler)

	commonMux := http.NewServeMux()
	commonMux.Handle("/user/", userMux)
	commonMux.HandleFunc("/ping", routes.PingRoute)
	commonMux.HandleFunc("/version", routes.VersionRoute)

	// Set common middlewares, from bottom to top
	commonHandler := corsMiddleware(commonMux)
	commonHandler = logMiddleware(commonHandler)
	commonHandler = panicMiddleware(commonHandler)

	server := http.Server{
		Addr:         listeningAddr + ":" + listeningPort,
		Handler:      commonHandler,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 10 * time.Second,
	}

	log.Printf("Starting server at %s:%s\n", listeningAddr, listeningPort)
	server.ListenAndServe()
}
