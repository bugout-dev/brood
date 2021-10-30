/*
Project configuration variables.
*/
package settings

import (
	"os"
	"time"
)

// Database configs
var BROOD_DB_URI string = os.Getenv("BROOD_DB_URI")
var BROOD_DB_MAX_IDLE_CONNS int = 30
var BROOD_DB_CONN_MAX_LIFETIME = 30 * time.Minute
