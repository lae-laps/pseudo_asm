/*	PSEUDOCODE Interpreter

	TODO´s:
	 - Implement comentaries - parse source as string - create split and look for "//", when find it, search index of start and end of commentary in current element of split, then add length of splits before, calculate global indices and delete

*/

package main

import (
	"fmt"
	"regexp"
	"runtime"
	"strings"
	"strconv"
)

var sourceCode string
var codeFlags int = 0

var Tokens = make(map[string]*regexp.Regexp)

func setDefaultTokenValues() error {
	var err error

	Tokens[":"], err = regexp.Compile("^:$"); if err != nil {return err}
	Tokens["+"], err = regexp.Compile("^\\+$"); if err != nil {return err}
	Tokens["-"], err = regexp.Compile("^-$"); if err != nil {return err}
	Tokens["*"], err = regexp.Compile("^\\*$"); if err != nil {return err}
	Tokens["/"], err = regexp.Compile("^/$"); if err != nil {return err}
	Tokens["("], err = regexp.Compile("^\\($"); if err != nil {return err}
	Tokens[")"], err = regexp.Compile("^\\)$"); if err != nil {return err}
	Tokens["="], err = regexp.Compile("^=$"); if err != nil {return err}
	Tokens[">"], err = regexp.Compile("^>$"); if err != nil {return err}
	Tokens["<"], err = regexp.Compile("^<$"); if err != nil {return err}
	Tokens["<>"], err = regexp.Compile("^<>$"); if err != nil {return err}
	Tokens["if"], err = regexp.Compile("^if$"); if err != nil {return err}
	Tokens["to"], err = regexp.Compile("^to$"); if err != nil {return err}
	Tokens["for"], err = regexp.Compile("^for$"); if err != nil {return err}
	Tokens["asign"], err = regexp.Compile("^<-$"); if err != nil {return err}
	Tokens["step"], err = regexp.Compile("^step$"); if err != nil {return err}
	Tokens["else"], err = regexp.Compile("^else$"); if err != nil {return err}
	Tokens["next"], err = regexp.Compile("^next$"); if err != nil {return err}
	Tokens["then"], err = regexp.Compile("^then$"); if err != nil {return err}
	Tokens["comment"], err = regexp.Compile("^//$"); if err != nil {return err}
	Tokens["endif"], err = regexp.Compile("^endif$"); if err != nil {return err}
	Tokens["while"], err = regexp.Compile("^while$"); if err != nil {return err}
	Tokens["until"], err = regexp.Compile("^until$"); if err != nil {return err}
	Tokens["array"], err = regexp.Compile("^array$"); if err != nil {return err}
	Tokens["input"], err = regexp.Compile("^input$"); if err != nil {return err}
	Tokens["newline"], err = regexp.Compile("^0nl$"); if err != nil {return err}
	Tokens["output"], err = regexp.Compile("^output$"); if err != nil {return err}
	Tokens["repeat"], err = regexp.Compile("^repeat$"); if err != nil {return err}
	Tokens["string"], err = regexp.Compile("^string$"); if err != nil {return err}
	Tokens["integer"], err = regexp.Compile("^integer$"); if err != nil {return err}
	Tokens["declare"], err = regexp.Compile("^declare$"); if err != nil {return err}
	Tokens["literalint"], err = regexp.Compile("^-?\\d+$"); if err != nil {return err}
	Tokens["endwhile"], err = regexp.Compile("^endwhile$"); if err != nil {return err}
	Tokens["literalchar"], err = regexp.Compile("'[ -~]{1}'"); if err != nil {return err}
	Tokens["literalstring"], err = regexp.Compile("\"[ -~]*\""); if err != nil {return err}
	
	return nil

}

func getToken(expr string) string {

	for token, regex := range Tokens {
		
		match := regex.MatchString(expr)
		if match {
			return token
		}
	}

	varRegex, err := regexp.Compile("^[a-zA-Z_$][a-zA-Z_$0-9]*$"); if err != nil {return "none"}

	if varRegex.MatchString(expr) {
		return "identifier"
	}

	return "none"
}

func lexer(source string) [][]string {
	if runtime.GOOS == "windows" {
		source = strings.ReplaceAll(source, "\r\n", "\n")
	}

	source = strings.ReplaceAll(source, "\t", " ")
	source = strings.TrimSpace(source)
	source = strings.ReplaceAll(source, "\n", " 0nl ")			// Use "0nl" as newline substitute -> use 0 so it cant be overwritten by a variable in sourcecode
	whitespaces := regexp.MustCompile(`\s+`)
	source = whitespaces.ReplaceAllString(source, " ")			// Replace multiple whitespaces with single whitespace 
	elements := strings.Split(source, " ")


	for i, element := range elements {
		elements[i] = strings.TrimSpace(element)
	}

	var objects []string

	for _, element := range elements {
		if (len(element) != 0) {
			objects = append(objects, strings.ToLower(element))
		}
	}

	tokens := make([][]string, len(objects))
	for i := range tokens {
    	tokens[i] = make([]string, 2)
	}

	for i, object := range objects {
		match := getToken(object)
		if match == "none" {
			throwError(fmt.Sprintf("unknown token: %s", object))
		}

		tokens[i][0] = match
		tokens[i][1] = object

		//debug(fmt.Sprintf("%s -> %s", object, match))
	}

	tokens = append(tokens, []string{"newline", "0nl"})

	return tokens

}

func isBlockInstruction(instruction string) (bool, string) {
	blockInstructions := [][]string{
		{"if", "endif"},
		{"for", "next"},
		{"repeat", "until"},
		{"while", "endwhile"}, 
		{"function", "endfunction"},
		{"procedure", "endprocedure"},
	}

	for _, inst := range blockInstructions {
		if instruction == inst[0] {
			return true, inst[1]
		}
	}

	return false, "none"
}

func parseLines(tree [][]string) [][][]string {
	var noComments [][][]string
	var doubleParseTree [][][]string
	var ret [][][]string
	var final [][][]string

	lastIndex := 0
	
	for i, element := range tree {
		var currentInstruction [][]string
		if element[0] == "newline" {
			for j := lastIndex; j < i; j++ {
				currentInstruction = append(currentInstruction, tree[j])
			}

			lastIndex = i + 1

			doubleParseTree = append(doubleParseTree, currentInstruction)
		}
	}

	for _, element := range doubleParseTree {
		if len(element) != 0 {
			ret = append(ret, element)
		}
	}
	
	for _, line := range ret {
		var tmp [][]string
		for _, element := range line {
			if element[0] == element[1] {
				m := []string{element[0]}
				tmp = append(tmp, m)
			} else {
				if element[1] == "<-" {
					tmp = append(tmp, []string{"asign"})
				} else {
					tmp = append(tmp, element)
				}
			}
		}
		final = append(final, tmp)
	}

	for _, line := range final {

		if len(line[0]) < 2 {
			noComments = append(noComments, line)
			continue
		}

		if (line[0][0] != "comment") {
			noComments = append(noComments, line)
		}
	}

	noComments = append(noComments, [][]string{{"EOF"}})						// Add an EOF token

	return noComments
}

func translate(tree [][][]string, start int, finish int) string {

	var bytecodes string

	for i := start; i < finish; i++ {

		match, delimiter := isBlockInstruction(tree[i][0][0])
				
		if match {
			
			changed := false
			delimiterIndex := 0
			count := 1

			for j := i + 1; j < len(tree); j++ {
				if tree[j][0][0] == delimiter {
					count -= 1
					if count <= 0 {
						delimiterIndex = j
						changed = true
						break
					}
				} else if tree[j][0][0] == tree[i][0][0] {
					count += 1
				}
			}

			if changed == false {
				throwSyntaxError(fmt.Sprintf("unclosed %s block", tree[i][0][0]), i)
			}

			debug(fmt.Sprintf("added new block from %d to %d", i, delimiterIndex))

			//translate(tree, i+1, delimiterIndex)
			
			if (tree[i][0][0] == "PROCEDURE") || (tree[i][0][0] == "FUNCTION") {
				// TODO: set code for procedures and functions
			} else {

				if len(tree[i]) <= 1 {
					throwSyntaxError("condition needed", i + 1)

				}
				condition := tree[i]
				condition = condition[1:]
				//debug(fmt.Sprintf("condition : %s", condition))

				switch tree[i][0][0] {
				case "while":
					bytecodes += translateWhile(condition, tree, i + 1, delimiterIndex)
				case "for":
					bytecodes += translateFor(condition, tree, i + 1, delimiterIndex)
				case "repeat":
					bytecodes += translateRepeatUntil(condition, tree, i + 1, delimiterIndex)
				case "if":
					bytecodes += translateIf(condition, tree, i + 1, delimiterIndex)
				default:
					throwError("uncaught exception : unknown blocktype")
					abort(1)
				}
			}
			
			i = delimiterIndex
		} else {
			// translate linear instructions
			bytecodes += translateInstruction(tree[i])
		}
	}
	return bytecodes
}

func compileExpression(raw [][]string, line int) string {

	/*var expr string

	for _, element := range raw {
		expr += element[1]
	}*/

	//var pos int	= 0				// position in expression
	//var currentToken string 	// current token in expression

	// Check if the expression is invalid

	var operators []string = []string{"+", "-", "*", "/"}
	var comparators []string = []string{">", "<", "<>", "="}

	// pass everything to a temporal expr to check for validity

	var expr [][]string

	for _, element := range raw {
		if (element[0] != "(") && (element[0] != ")") {
			expr = append(expr, element)
		}
	}

	operatorsFound := 0
	comparatorsFound := 0
	
	for i, element := range expr {
		for _, match := range comparators {
			if match == element[0] {
				comparatorsFound += 1
				if len(expr) > i + 1 {
					for _, match := range comparators {
						if match == expr[i + 1][0] {
							throwSyntaxError("cannot follow a comparator by another comparator", line)
						}
					}
				}
			}
		}
		for _, match := range operators {
			if match == element[0] {
				operatorsFound += 1
				if len(expr) >= i {
					for _, match := range operators {
						if match == expr[i + 1][0] {
							throwSyntaxError("cannot follow an operator by another operator", line)
						}
					}
				}
			}
		}
	}
	
	for _, match := range operators {
		if (expr[0][0] == match) || (expr[len(expr) - 1][0] == match) {
			throwSyntaxError("invalid expression: expression cannot start or end with an operator", line)
		}
	}
	
	for _, match := range comparators {
		if (expr[0][0] == match) || (expr[len(expr) - 1][0] == match) {
			throwSyntaxError("invalid expression: expression cannot start or end with a comparator", line)
		}
	}


	for i, element := range expr {
		if i % 2 != 0 {
			found := false
			for _, match := range comparators {
				if match == element[0] {
					found = true
					break
				}
			}
			for _, match := range operators {
				if match == element[0] {
					found = true
					break
				}
			}
			if found == false {
				throwSyntaxError(fmt.Sprintf("expected an operator or comparator at position %d", i + 2), line)
			}
		} else {
			found := false
			for _, match := range comparators {
				if match == element[0] {
					found = true
					break
				}
			}
			for _, match := range operators {
				if match == element[0] {
					found = true
					break
				}
			}
			if found {
				throwSyntaxError(fmt.Sprintf("unexpected operator or comparator at position %d", i + 2), line)
			}
			if (element[0] != "identifier") && (element[0] != "literalint") {
				throwSyntaxError(fmt.Sprintf("expected identifier at position %d", i + 2), line)
			}
		}
	}

	// check for parentheses

	opening := 0
	closing := 0

	for _, element := range raw {
		if element[0] == "(" {
			opening += 1
		} else if element[0] == ")" {
			closing += 1
		}
	}

	if opening != closing {
		throwSyntaxError("unmatched parenthesis in expression", line)
	}

	count := 1
	changed := false
	lastIndex := 0

	var element []string

	for i := 0; i < len(raw); i++ {
		element = raw[i]
		if element[0] == "(" {
			for j := i + 1; j < len(raw); j++ {
				if raw[j][0] == ")" {
					count -= 1
					if count <= 0 {
						lastIndex = j
						changed = true
						break
					}
				} else if raw[j][0] == "(" {
					count += 1
				}
			}

			if changed == false {
				throwSyntaxError("unclosed parenthesis in expression", line)
			}
			
			var tmp [][]string

			for j := i + 1; j < lastIndex; j++ {
				tmp = append(tmp, raw[j])
			}

			fmt.Println(sprintInstruction(tmp))

			i = lastIndex
		}
	}

	return "none"

}

func translateInstruction(instruction [][]string) string {
	return fmt.Sprintf(" > %s\n", sprintInstruction(instruction))
}

func translateWhile(condition [][]string, code [][][]string, start int, end int) string {

	var bytecodes string

	if len(condition) < 1 {
		throwSyntaxError("no condition provided for while", start)
	}

	expr := condition[0:]

	compiledExpression := compileExpression(expr, start)

	bytecodes += fmt.Sprintf("%x:\n", codeFlags)

	codeFlags += 1

	bytecodes += compiledExpression

	bytecodes += fmt.Sprintf("jne $%x\n", codeFlags)

	bytecodes += translate(code, start, end) + "\n"

	bytecodes += fmt.Sprintf("jmp $%x\n", codeFlags - 1)

	bytecodes += fmt.Sprintf("%x:\n", codeFlags)

	codeFlags += 1

	return bytecodes

}

func translateFor(condition [][]string, code [][][]string, start int, end int) string {

	var min int
	var max int
	var err error
	var increment int
	var bytecodes string

	if len(condition) < 5 {
		throwSyntaxError("incomplete condition in for loop", start)
	}

	if (condition[0][0] != "identifier") || (condition[1][0] != "asign") || ((condition[2][0] != "literalint") && (condition[2][0] != "identifier")) || (condition[3][0] != "to") || ((condition[4][0] != "literalint") && (condition[4][0] != "identifier")) {
		throwSyntaxError("invalid condition in for loop", start)
	}

	if end - start < 1 {
		throwSyntaxError("expected code block after for", start)
	}

	if len (condition) == 5 {
		increment = 1
	} else {
		if len(condition) < 7 {
			throwSyntaxError("expected expresion for step increment", start)
		}
		if len(condition) > 7 {
			throwSyntaxError("too many values for condition", start)
		}

		if (condition[5][0] != "step") || ((condition[6][0] != "literalint") && (condition[6][0] != "identifier")) {
			throwSyntaxError("invalid expression in for loop. Expected STEP increment", start)
		}

		if condition[6][0] == "identifier" {
			increment = getDataFlag(condition[6][1])
		} else {
			increment, err = strconv.Atoi(condition[6][1])
			if err != nil {throwSyntaxError("exception during conversion of condition to integers", start)}
		}
	}

	if condition[4][0] == "literalint" {
		max, err = strconv.Atoi(condition[4][1])
		if err != nil {throwSyntaxError("exception during conversion of condition to integers", start)}
	} else {
		max = getDataFlag(condition[4][1])
	}

	if condition[2][0] == "literalint" {
		min, err = strconv.Atoi(condition[2][1])
		if err != nil {throwSyntaxError("exception during conversion of condition to integers", start)}
	} else {
		min = getDataFlag(condition[2][1])
	}

	iterator := getDataFlag(condition[0][1])

	bytecodes += fmt.Sprintf("mov %d, &%x\n", min, iterator)

	bytecodes += fmt.Sprintf("%x:\n", codeFlags)

	codeFlags += 1													// Codeflags must be incremented here and not at end since it is a recursive algorithm

	bytecodes += translate(code, start, end) + "\n"
	
	bytecodes += fmt.Sprintf("add %d, &%x\n", increment, iterator)
	
	bytecodes += fmt.Sprintf("cmp &%x, %d\n", iterator, max)
	
	bytecodes += fmt.Sprintf("jle $%x\n", codeFlags - 1)
	

	// set flag at  start : i <- i + 1
	// instructions
	// cmp i, max
	// jle start

	return bytecodes

}


func translateRepeatUntil(condition [][]string, code [][][]string, start int, end int) string {return "none"}
func translateIf(condition [][]string, code [][][]string, start int, end int) string {return "none"}

func getDataFlag(flagname string) int {
	return 10
}

func main() {
	source := `
	
	// some comment here
	
	somecode

	// some other comment here
	FOR x <- 3 to a STEP -4
		start
		somecode
		somemorecode
		end
	NEXT i


	WHILE somecondition > 2 + ( x * 8 / 6 ) - ( 3 * 2 - x / 54 + 3 )

	start2
	dosomestuff
	andsomemore
	end2

	ENDWHILE

	`

	err := setDefaultTokenValues()
	if err != nil {
		throwError("could not asign all regexp for tokens")
		abort(1)
	}

	sourceCode = source

	tokens := lexer(source)

	doubleSplitTree := parseLines(tokens)

	bytecodes := translate(doubleSplitTree, 0, len(doubleSplitTree))

	fmt.Println(bytecodes)

}
