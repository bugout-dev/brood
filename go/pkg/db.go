/*
Connections to database.
*/
package brood

import (
	"database/sql"
	"log"

	_ "github.com/lib/pq"

	settings "github.com/bugout-dev/brood/go/configs"
)

// SessionDB represents the database session store
type SessionDB struct {
	DB *sql.DB
}

// Initialize and return new session instance
func InitSessionDB() *SessionDB {
	db, err := sql.Open("postgres", settings.BROOD_DB_URI)
	if err != nil {
		// DSN parse error or another initialization error
		log.Fatal(err)
	}

	// Set the maximum number of concurrently idle connections,
	// by default sql.DB allows a maximum of 2 idle connections.
	db.SetMaxIdleConns(settings.BROOD_DB_MAX_IDLE_CONNS)

	// Set the maximum lifetime of a connection.
	// Longer lifetime increase memory usage.
	db.SetConnMaxLifetime(settings.BROOD_DB_CONN_MAX_LIFETIME)

	sessionDB := &SessionDB{DB: db}
	return sessionDB
}
