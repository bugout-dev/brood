/*
Handle user routes for Brood API.
*/
package routes

import (
	"encoding/json"
	"fmt"
	"mime"
	"net/http"
	"strings"

	actions "github.com/bugout-dev/brood/go/cmd/actions"
	brood "github.com/bugout-dev/brood/go/pkg"
)

// UserServer instance
type userServer struct {
	processor *actions.UserProcessor
	sessionDB *brood.SessionDB
}

// Initialize new user instance with database connection
func NewUserServer(sessionDB *brood.SessionDB) *userServer {
	processor := actions.New()
	return &userServer{processor: processor, sessionDB: sessionDB}
}

// Handle user routes
func (us *userServer) UserHandler(w http.ResponseWriter, r *http.Request) {
	if r.URL.Path == "/user/" {
		switch {
		case r.Method == http.MethodGet:
			us.getUserRoute(w, r)
		case r.Method == http.MethodPost:
			us.createUserRoute(w, r)
		default:
			http.Error(w, fmt.Sprintf("Unacceptable method provided %v", r.Method), http.StatusMethodNotAllowed)
			return
		}
	} else {
		paths := strings.Split(strings.Trim(r.URL.Path, "/"), "/")
		pathsLen := len(paths)
		if pathsLen != 2 {
			http.Error(w, "Unacceptable path", http.StatusBadRequest)
			return
		}
		switch {
		case r.Method == http.MethodDelete:
			us.deleteUserRoute(w, r)
		default:
			http.Error(w, fmt.Sprintf("Unacceptable metod provided %v", r.Method), http.StatusMethodNotAllowed)
			return
		}
	}
}

// Get user from database
func (us *userServer) getUserRoute(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Get user")
}

// Add user to database
func (us *userServer) createUserRoute(w http.ResponseWriter, r *http.Request) {
	contentType := r.Header.Get("Content-Type")
	mediatype, _, err := mime.ParseMediaType(contentType)
	if err != nil {
		http.Error(w, "Expected multipart/form-data Content-Type", http.StatusUnsupportedMediaType)
		return
	}
	if mediatype != "application/x-www-form-urlencoded" {
		http.Error(w, "Expected multipart/form-data Content-Type", http.StatusUnsupportedMediaType)
	}
	r.ParseForm()
	user, err := us.processor.CreateUserAction(us.sessionDB, r.Form.Get("username"), r.Form.Get("email"), r.Form.Get("password"))
	if err != nil {
		http.Error(w, err.Error(), http.StatusConflict)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(user)
}

// Delete user from database
func (us *userServer) deleteUserRoute(w http.ResponseWriter, r *http.Request) {
	fmt.Println("Delete user")
}
