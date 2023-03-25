// IO handling

package main

import (
	"os"
	"fmt"
	"strings"
)

var DEBUG bool = false

func debug(msg string) {
	if DEBUG {
		fmt.Printf("debug: %s\n", msg)
	}
}

func throwError(msg string) {
	fmt.Printf("error: %s\n", msg)
	abort(2)
}

func throwSyntaxError(msg string, linenumber int) {
	split := strings.Split(sourceCode, "\n")
	count := 0
	for i, element := range split {
		element = strings.TrimSpace(element)
		if (len(element) >= 1) && (strings.HasPrefix(element, "//") == false) {
			count += 1
			if count == linenumber {
				linenumber = i + 1
			}
		}
	}
	fmt.Printf("syntax error: %s : %d\n\t%s\n", msg, linenumber, strings.TrimSpace(split[linenumber - 1]))
	abort(1)
}

func sprintInstruction(array [][]string) string {
	var instruction string = ""
	for _, element := range array {
		if len(element) > 1 {
			instruction = fmt.Sprintf("%s %s", instruction, element[1])
		} else {
			instruction = fmt.Sprintf("%s %s", instruction, element[0])
		}
	}
	return strings.TrimSpace(instruction)
}

func abort(code int) {
	//fmt.Printf("exit code: %d\n", code)
	os.Exit(code)

	/*	0 -> No error
		1 -> Syntax error
		2 -> Undetermined error
		3 -> Virtual Machine core error
	*/

}
