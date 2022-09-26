package main

import (
	//"crypto/rand"
	"fmt"
	randMath "math/rand"
	"net/http"
	"time"

	"github.com/gin-gonic/gin"
)

type players struct {
    ID     int64  `json:"id"`
    Color  string  `json:"color"`
    Input string  `json:"input"`
    LastInput  int64 `json:"lastInput"`
}

type playersSecret struct {
    ID     int64  `json:"id"`
    Password string `json:"password"`
}

type playerAssign struct {
    ID     int64  `json:"id"`
    Password string `json:"password"`
    Color  string  `json:"color"`
}

const letterBytes = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
const (
    letterIdxBits = 6                    // 6 bits to represent a letter index
    letterIdxMask = 1<<letterIdxBits - 1 // All 1-bits, as many as letterIdxBits
    letterIdxMax  = 63 / letterIdxBits   // # of letter indices fitting in 63 bits
)

func RandStringBytesMaskImpr(n int) string {
    b := make([]byte, n)
    // A rand.Int63() generates 63 random bits, enough for letterIdxMax letters!
    for i, cache, remain := n-1, randMath.Int63(), letterIdxMax; i >= 0; {
        if remain == 0 {
            cache, remain = randMath.Int63(), letterIdxMax
        }
        if idx := int(cache & letterIdxMask); idx < len(letterBytes) {
            b[i] = letterBytes[idx]
            i--
        }
        cache >>= letterIdxBits
        remain--
    }

    return string(b)
}


// copied from https://mokole.com/palette.html
var colors25 = [25]string {"#000080", "#0000ff", "#00bfff", "#00ced1", "#00ff7f", "#1e90ff", "#228b22", "#483d8b", "#708090", "#7cfc00", "#800000", "#808000", "#8a2be2", "#8b008b", "#8fbc8f", "#9acd32", "#dda0dd", "#e0ffff", "#e9967a", "#f0e68c", "#ff00ff", "#ff1493", "#ff6347", "#ff8c00", "#ffd700"}

var colors20 = [20]string {"#0000cd", "#008000", "#00ff00", "#00ffff", "#191970", "#1e90ff", "#7f0000", "#808080", "#87cefa", "#90ee90", "#ba55d3", "#bdb76b", "#dda0dd", "#fa8072", "#ff00ff", "#ff1493", "#ff4500", "#ffa500", "#ffe4e1", "#ffff54"}

var usedColor = colors20

// will be filled up in main based on usedColor above
var playersData = [len(usedColor)]players {
}

var playersSecretData = [len(usedColor)]playersSecret {
}

func getInput(c *gin.Context) {
    var params = c.Request.URL.Query()
    //fmt.Println(params);

    // test if pw and input exist:
    pw, pwOk := params["pw"]
    input, inputOk := params["input"]

    if pwOk && inputOk {
        var matching = -1
        for i, v := range playersSecretData {
            if v.Password == pw[0] {
                matching = i
            }
        }
        if (matching == -1){
            // no matching player with that password found
            //c.IndentedJSON(http.StatusForbidden, playersData)
            c.String(http.StatusForbidden, "Wrong Password!")
        } else {
            // password correct, assing input
            playersData[matching].Input = input[0];
            playersData[matching].LastInput = time.Now().Unix();
            c.String(http.StatusAccepted, "Input updated")
        }
    } else {
        // just return the players
        //c.JSON(http.StatusOK, playersData)
        c.JSON(http.StatusOK, playersData)
    }
}

func getSecret(c *gin.Context) {
    // test if pw exist and is correct:
    pw, pwOk := c.Request.URL.Query()["pw"]
    if pwOk && pw[0] == "secret" {
        c.JSON(http.StatusOK, playersSecretData)
    } else {
        c.String(http.StatusForbidden, "Wrong Password")
    }

}

func getAssign(c *gin.Context) {
    var currentTime int64 = time.Now().Unix()
    matching := -1
    for i, v := range playersData {
        if v.LastInput < currentTime - 10 { // Delay for disconnecting
            matching = i
            break
        }
    }
    if(matching != -1){
        newPw := RandStringBytesMaskImpr(32)
        playersSecretData[matching].Password = newPw
        playersData[matching].LastInput = currentTime
        playersData[matching].Input = ""
        c.JSON(http.StatusOK, playerAssign{Password: newPw, Color: playersData[matching].Color, ID: playersData[matching].ID})
    } else {
        c.String(http.StatusInsufficientStorage, "No free Player available :(")
    }
}

func getTea(c *gin.Context) {
    c.String(http.StatusTeapot, "Cannot brew coffee, I am only a teapot")
}

func redir(c *gin.Context) {
    c.Redirect(http.StatusPermanentRedirect, "/tea")
}

func getClient(c *gin.Context) {
    c.File("./client.html")
}


func main() {
    randMath.Seed(time.Now().UnixNano())

    for i := range playersData {
        playersData[i] = players {ID: int64(i), Color: usedColor[i], Input: "", LastInput: 0}
    }

    for i := range playersSecretData {
        playersSecretData[i] = playersSecret{ID: int64(i), Password: RandStringBytesMaskImpr(32)}
    }

    fmt.Println(playersData)
    fmt.Println(playersSecretData)
    
    gin.SetMode(gin.ReleaseMode)
    router := gin.Default()

    router.GET("/input", getInput)
    router.GET("/secret", getSecret)
    router.GET("/assign", getAssign)
    router.GET("/tea", getTea)
    router.GET("/", redir)
    router.GET("/client", getClient)

    // use this for outside of Docker
    router.Run("localhost:8080")
    //router.Run("web-input:8080")
}