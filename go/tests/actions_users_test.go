package test

import (
	"reflect"
	"testing"

	"github.com/google/uuid"

	actions "github.com/bugout-dev/brood/go/cmd/actions"
	brood "github.com/bugout-dev/brood/go/pkg"
)

type TestCase struct {
	Key     string
	User    *brood.User
	IsError bool
}

func TestGetUser(t *testing.T) {
	userID, _ := uuid.Parse("4e4f1efb-21bf-4c69-b2ae-20e80ef85809")
	cases := []TestCase{
		TestCase{"ok", &brood.User{ID: userID}, false},
		TestCase{"fail", nil, true},
		TestCase{"not_exist", nil, true},
	}

	for caseNum, item := range cases {
		u, err := actions.GetUserAction(item.Key)

		if item.IsError && err == nil {
			t.Errorf("[%d] expected error, got nil", caseNum)
		}
		if !item.IsError && err != nil {
			t.Errorf("[%d] unexpected error", caseNum, err)
		}
		if !reflect.DeepEqual(u, item.User) {
			t.Errorf("[%d] wrong results: got %+v, expected %+v",
				caseNum, u, item.User)
		}
	}

}
