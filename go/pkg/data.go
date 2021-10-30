/*
Schema for Brood API.
*/
package brood

type PingResponse struct {
	Status string `json:"status"`
}

type VersionResponse struct {
	Version string `json:"version"`
}

type UserRequest struct {
	Username string `json:"username"`
}
