/*
Handle common routes for Brood API.
*/
package routes

import (
	"encoding/json"
	"net/http"

	"github.com/bugout-dev/brood/go/pkg"
)

func PingRoute(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	res := brood.PingResponse{Status: "ok"}
	json.NewEncoder(w).Encode(res)

}

func VersionRoute(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	res := brood.VersionResponse{Version: brood.Version}
	json.NewEncoder(w).Encode(res)
}
