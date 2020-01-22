
CPU_WIDTH = 16
#SMBS is a dictionary of all the symbols/identifiers
SMBS = {"(" : "START_LABEL",
        ")" : "END_LABEL",
        "@" : "SET_A_REG",
        "M" : "SET_M",
        "/" : "INITIATE_COMMENT",
        "A" : "C_OR_JMP",
        "D" : "C_OR_JMP",
        "M" : "C_OR_JMP",
        "0" : "C_OR_JMP", #for something like 0;JMP
        ";" : "JMP_IDENTIFIER",
        "=" : "C_IDENTIFIER"
        }
OPERATIONS = {
        "|" : "OR",
        "&" : "AND",
        "+" : "ADD",
        "-" : "SUBTRACT"
              }


SINGLE_OPERATIONS = {
    "-" : "NEGATE",
    "!" : "NOT"
    }

#JMPINST is a dictionary of all the jump symbols and their equivilent binary, I want to change this because it's just a direct binary translation and thats what i'm avoiding in this project
JUMPINST = {
    "JMP" : "111",
    "JGT" : "001",
    "JEQ" : "010",
    "JGE" : "011",
    "JLT" : "100",
    "JNE" : "101",
    "JLE" : "110"
    }

PREDEFINED_SYMBOLS = { #stuff like screen that the locations are predefined
    "SP" : "0",
    "LCL" : "1",
    "ARG" : "2",
    "THIS" : "3",
    "THAT" : "4",
    "SCREEN" : "16384",
    "KBD" : "24576",
}
#R is also in there, but will be handled later


#im basically using these as enums
#TODO: make these a lot less messy, and less of the same thing basically
C_SINGLE_OPERATION = "SINGLE_OPERATION"
C_OPERATION = "C_OPERATION"
INT_DATA_IDENTIFIER = "INT_DATA"
VARIABLE_DATA_IDENTIFIER = "VARIABLE_DATA"
C_TARGET_IDENTIFIER = "C_TARGET"
C_DATA_INT = "C_DATA_INT"
C_DATA_SYMBOL = "CN_DATA_SYMBOL"
C_SINGLE_DATA_INT = "C_SINGLE_DATA_INT"
C_SINGLE_DATA_SYMBOL = "C_SINGLE_DATA_SYMBOL"
A_REG_IDENTIFIER = "SET_A_REG"
JMP_TYPE = "JMP_TYPE"
JMP_TARGET = "JMP_TARGET"
LABEL_IDENTIFIER = "LABEL"

class Assembler():
    def __init__(self):
        #va is a dictionary that will contain the variable name and the appropriate binary address, so to add a variable it would follow {"hello" : "0001001101"} or similar
        #lastVDA is the last variable DECIMAL address so the next one can be a step up from it
        self.VA = {}
        self.lastVDA = 15 #va starts at bit 16, so make it 15 so it knows to increment to 16 the next time
        self.newLine = "\n"


        self.labelDic = {} #this is a dictionary of every label and it's address which is determined by lastPCLine, this is NOT A PC(program counter) DICTIONARY, it only holds the addresses for the labels
        self.PCLine = 0 #The pc line needs to start at 1 so be at 0, This increments every line 


    def assemble(self, source, debug=False):
        self.sourceList = source

        self.debug = debug #just for printing out stuff

        return(self.decodeLines(self.sourceList))

    def fixedBinSize(self, size, binary): #used to add remaining zeros to a binary number if its not 16 numbers big(or size)
        rawBinary = binary[2:] #we have to ignore the first 2 characters because they are the 0b
        binSize = len(rawBinary)
        for numbersRemaining in range(size-binSize):
            rawBinary = "0" + rawBinary
        return("0b" + rawBinary) #just put it back for consistency, will just remove later tho

    #formats the source ints into a workable binary format
    def formatBinary(self, line, width=CPU_WIDTH):
        out = self.fixedBinSize(width, bin(int(line)))[2:]

        if(self.debug): print("Formatting binary...", line, "->", out)

        return(out)

    #this is where it decodes symbols and non-binary stuff to a binary format
    def decodeLines(self, lines):

        if(self.debug): print("\n========\n\n-> PARSING FOR JUMP LABELS...")
        #This first run is to find labels, and add their addresses to memory :
        for line in lines:
            if(len(line)>1): #if its not blank(1 because \n is a char)
                self.PCLine+=1 #next line in PC

                segmentedLine = self.segmentLineInstructions(line, False) #False means don't ignore labels

                if(len(segmentedLine)>0): #if its not blank
                    self.handleLabels(segmentedLine)

        if(self.debug): print("\n========\n\n")

        finalInstructions = ""
        for line in lines:

            if(self.debug): print("\n-> ON LINE---", line[:len(line)-1]) #linelen - 1 cuz it will get rid of the \n on the end, instead have the \n on top of this line

            #send the output of the segmentLineInstructions function to buildInstruction
            segmentedLine = self.segmentLineInstructions(line, True)

            if(self.debug): print("Line segmented into...", segmentedLine)

            finishedInstruction = self.buildInstruction(segmentedLine)

            if(len(finishedInstruction)>0):
                finalInstructions = finalInstructions + (finishedInstruction + self.newLine)

                if(self.debug): print("Assembled line: ", finishedInstruction)
                

        return(finalInstructions)

    def representsInt(self, stringValue):
        try:
            int(stringValue)
            return(True)
        except:
            return(False)

    #checks a line for symbol, and returns a multi dimensional list like: [["@","SET_A_REG"],["173","INT_DATA"]].
    def segmentLineInstructions(self, line, ignoreLabels=True):
        instructions = []
        stringCache = ""
        stringCacheOn = False
        ignoreLine = False


        #these bools help identify which symbols have been detected earlier in the line
        isAInstruction = False
        isCInstruction = False
        isLabel = False

        characterIndex = 0
        #check all characters passed for a matching symbol
        while characterIndex < len(line): #cant use a for loop here cuz we have to manually increase character index if needed

            #match the current symbol to the dictionary(if it's the first character NOTE: used: https://able.bio/rhett/check-if-a-key-exists-in-a-python-dictionary--73iajoz
            if(characterIndex == 0 and line[characterIndex] in SMBS and not ignoreLine): #only for the first character in the line
                if(SMBS[line[characterIndex]] == "INITIATE_COMMENT"): #NOTE: right now it only supports comments that start at the begining of the line, not after an instruction
                    ignoreLine = True

                    if(not ignoreLabels): #we have to ignore this line in the PC conuter cuz its not valid
                        self.PCLine-=1

                elif(SMBS[line[characterIndex]] == "SET_A_REG"): #is an a instruction
                    isAInstruction = True
                    instructions.append([line[characterIndex], A_REG_IDENTIFIER])
                    stringCacheOn = True
                    characterIndex+=1

                elif(SMBS[line[characterIndex]] == "START_LABEL" and not ignoreLabels): #its a label
                    isLabel = True
                    stringCacheOn = True
                    characterIndex+=1 #dont append the current char to instructions because we don't want the parentheses

                elif(SMBS[line[characterIndex]] == "C_OR_JMP"):
                    #we have to identify if its a c instruction or jumping from a d or m
                    if(SMBS[line[characterIndex+1]] == "C_IDENTIFIER"): #check if the next index is =, so then we know its a c instruction. HOWEVER: if it is another a d or m, this can mean its an ad or am or something like that c destination
                        isCInstruction = True
                        stringCacheOn = True
                        instructions.append([line[characterIndex], C_TARGET_IDENTIFIER])
                        characterIndex+=2

                    elif(SMBS[line[characterIndex+1]] == "C_OR_JMP"): #We now can assume its a c instruction because jmp instructions cannot have two targets so like da am or something
                        if(SMBS[line[characterIndex+2]] == "C_IDENTIFIER"): #ok so we only have 2 targets so like ad md etc...
                            isCInstruction = True
                            stringCacheOn = True
                            instructions.append([line[characterIndex:characterIndex+2], C_TARGET_IDENTIFIER])
                            characterIndex+=3

                        elif(SMBS[line[characterIndex+2]] == "C_OR_JMP"): #now it means we have three targets so adm or something
                            if (SMBS[line[characterIndex+3]] == "C_IDENTIFIER"): #just make sure
                                isCInstruction = True
                                stringCacheOn = True
                                instructions.append([line[characterIndex:characterIndex+3], C_TARGET_IDENTIFIER])
                                characterIndex+=4

                    elif(SMBS[line[characterIndex+1]] == "JMP_IDENTIFIER"): #its a jmp
                        instructions.append([line[characterIndex], JMP_TARGET]) #append the target
                        characterIndex+=2 # get to the three letter jmp type
                        instructions.append([line[characterIndex:characterIndex+3], JMP_TYPE])
                        characterIndex+=3
                        

            #handle all of the string caching:
            if(stringCacheOn and not ignoreLine):
                if(line[characterIndex] != self.newLine): #make sure the current line is not a new line though
                    stringCache = stringCache + line[characterIndex]

                if(isAInstruction):
                    if(characterIndex == len(line)-1): #if we are at the end of line, this is the main reason comments don't work unless they are on their own line, perhapes later I can just make it detect a whitespace?
                        stringCacheOn = False
                        #now we have the full cached data that comes after @ so identify whether its integer data or variable variable data
                        if(self.representsInt(stringCache)):
                            instructions.append([stringCache, INT_DATA_IDENTIFIER])
                        else:
                            instructions.append([stringCache, VARIABLE_DATA_IDENTIFIER])

                elif(isLabel):
                    if(stringCache[len(stringCache)-1] in SMBS):
                        if(SMBS[stringCache[len(stringCache)-1]] == "END_LABEL"): #well this will work with a comment at the end because instead of seeing the end of the line it just detects if the last chracter is the label )
                            stringCacheOn = False
                            labelName = stringCache[:len(stringCache)-1] #to remove the last )
                            instructions.append([labelName, LABEL_IDENTIFIER])

                elif(isCInstruction):
                    if(characterIndex == len(line)-1):
                        stringCacheOn = False
                        if(len(stringCache) == 1): #it must be a single target such as A D or M
                                if(self.representsInt(stringCache[0])):
                                    instructions.append([stringCache, C_SINGLE_DATA_INT])
                                else:
                                    instructions.append([stringCache, C_SINGLE_DATA_SYMBOL])

                        elif(len(stringCache) == 2): #this means its a single operation so like !d
                                instructions.append([stringCache[0], C_SINGLE_OPERATION])
                                if(self.representsInt(stringCache[1])):
                                    instructions.append([stringCache[1], C_SINGLE_DATA_INT])
                                else:
                                    instructions.append([stringCache[1], C_SINGLE_DATA_SYMBOL])
                        elif(len(stringCache) == 3): #this means its something like a-d
                                if(self.representsInt(stringCache[0])):
                                    instructions.append([stringCache[0], C_SINGLE_DATA_INT])
                                else:
                                    instructions.append([stringCache[0], C_SINGLE_DATA_SYMBOL])

                                instructions.append([stringCache[1], C_OPERATION])

                                if(self.representsInt(stringCache[2])):
                                    instructions.append([stringCache[2], C_SINGLE_DATA_INT])
                                else:
                                    instructions.append([stringCache[2], C_SINGLE_DATA_SYMBOL])
            characterIndex += 1


        return(instructions)

    def handleLabels(self, data):
        
        if(data[0][1] == LABEL_IDENTIFIER):
            self.PCLine-=1 #we have to subtract the current line because the label is not really a valid line

            labelName = data[0][0]
            #append the label to the dictionary with the appropriate line address defined by the pc line
            self.labelDic[labelName] = self.formatBinary(self.PCLine, width=CPU_WIDTH-1)

            if(self.debug): print("Found label:", labelName, "at line address:", self.PCLine)
            if(self.debug): print("Label dictionary is now:", self.labelDic)


    def getCAcode(self, data, isC):
        #the if statements add on top of each other in their orders
        c = ["0","0","0","0","0","0"] #c1,c2,c3,c4,c5,c6 -> nx,zx,ny,zy,f,no
        a = "0"


        operationData = data[1:]
        opDataLen = len(operationData)
        operation = ""

        if(not isC):
            operationData = data[0] #because it is a JMP, so we need to fetch to code to use for the c instruction to get the data from, so this is like a 0 or D  #weird, i didnt know print("a", "b") would put a space in between them
            #NOTE that the c values represent the place that it's getting the values to compare, which it will jump to a if it passes the check.

        #search for m AFTER THE DESTINATION, which would be replacing A
        for sec in data:
            if(sec[0] == "M" and sec[1] != C_TARGET_IDENTIFIER):
                a = "1" 
                if(self.debug): print("Found an M in c inputs, setting a to 1...", sec)

        

        #NOTE: & operation is just all 0's so there is nothing to match it
        if(opDataLen == 1 or opDataLen == 2):
            
            if(opDataLen == 1):#something like D or A or M
                target = operationData[0][0]
            elif(opDataLen == 2): #for stuff like !A or -D
                 target = operationData[1][0]
                 operation = operationData[0][0]
                 
            if(target == "D"):
                #this is the from symbol
                c[2:4] = "11" #xx11xx
            elif(target == "A" or target == "M"):
                c[0:2] = "11" #11xxxx
            #this is a bit icky, i was trying to get away from straight definitons
            elif(target == "0"):
                c = ["1","0","1","0","1","0"]
            elif(target == "1"):
                c = ["1","1","1","1","1","1"]
            #handle operations
            if(operation!="" and SINGLE_OPERATIONS[operation] == "NOT"):
                c[5] = "1" #xxxxx1
            if(operation!="" and SINGLE_OPERATIONS[operation] == "NEGATE"):
                if(target == "1"):
                    c[3:] = "010"
                else:
                    c[4:] = "11" #xxxx11
        elif(opDataLen == 3): #if something like D-A or A+1
            dat1 = operationData[0][0]
            operation = operationData[1][0]
            dat2 = operationData[2][0]

            if(dat2 == "1"): #if its like D+1 or A-1
                if(dat1 == "D"):
                    c[2:4] = "11" #xx11xx
                elif(dat1 == "A" or dat1 == "M"):
                    c[0:2] = "11" #11xxxx
                
                if(OPERATIONS[operation] == "ADD"): #x1x111
                    c[1] = "1"
                    c[3:6] = "111"
                elif(OPERATIONS[operation] == "SUBTRACT"): #xxxx1x
                    c[4] = "1"
            
            else: #if dat2 is not 1 so most likely A/D/M operation A/D/M
                if(OPERATIONS[operation] == "ADD"):
                    c[4] = "1" #xxxx1x
                elif(OPERATIONS[operation] == "SUBTRACT"):
                    c[4:6] = "11" #xxxx11

                    if(dat1 == "D"):
                        c[1] = "1" #x1xxxx
                    elif(dat1 == "A" or dat1 == "M"):
                        c[3] = "1" #xxx1xx

                elif(OPERATIONS[operation] == "AND"):
                    c = ["0","0","0","0","0","0"] #redundant but im putting it here for consistency

                elif(OPERATIONS[operation] == "OR"):
                     c = ["0","1","0","1","0","1"]
            
        if(isC): 
            if(self.debug): print("Operation is: ", operation)
            if(self.debug): print("C:", "".join(c), "A:", a)



        return("".join(c), a)

    def getDCode(self, data):
        #IMPORTANT NOTE:
        #ORDER OF BOOK IS AMD FOR DESTINATION, THIS IS NOT TRUE, ACTUAL ORDER IS ADM

        d = ["0", "0", "0"]
        for char in data[0][0]: #data[0][0] is the target
            if(char == "A"):
                d[0] = "1" #remember ADM, not AMD
            elif(char == "D"):
                d[1] = "1"
            elif(char == "M"):
                d[2] = "1"

        if(self.debug): print("Destination number from type:", data[0][0], "->", "".join(d))

        return("".join(d))

    def getJMPCode(self, data):
        #get the last 3 codes for the c instruction, which only matter when a jump c instruction is happening

        jmp = ["0", "0", "0"]

        JMPtype = data[1][0] #the type of jmp

        jmp = JUMPINST[JMPtype]
        
        if(self.debug): print("Jump code from type is:", JMPtype, "->", jmp)

        #The logic behind the instructions follows: j1 - out<0, j2 - out=0, j3 - out>3, but i'm just using a dictionary so it doesn't matter too much.

        return("".join(jmp))
        


        
                
            
        

    """this function actually takes in the list produced by checkForSymbol and it will for example for [["@","SET_A_REG"],["173","BIN_DATA"]],
it will see that the first symbol is @ so start listening for data to put in a.

It will see that the next one is BIN_DATA, so it will just know that its a direct translation.
If its VARIABLE_DATA it will know to create a new entry if the variable name does not exist with the next memory address,
or it will reference the already existing address, and set it memory location to A"""

    def buildInstruction(self, sourceData):
        
        instruction = ""
        for segmentIndex in range(len(sourceData)):
            if(sourceData[segmentIndex][1] == A_REG_IDENTIFIER):
                
                if(self.debug): print("Current instruction type is A")

                if(sourceData[segmentIndex+1][1] == VARIABLE_DATA_IDENTIFIER):

                    if(sourceData[segmentIndex+1][0] in self.labelDic): #if its a label address
                        var = self.labelDic[sourceData[segmentIndex+1][0]]
                        
                        if(self.debug): print("A instruction is the label:", sourceData[segmentIndex+1][0], "->", var)
                        
                        instruction = ("0" + var)

                    else:

                        if(self.debug): print("A instruction is the variable:", sourceData[segmentIndex+1][0])

                        #handle the variable name, which will act as a pointer to a memory location
                        if(sourceData[segmentIndex+1][0] in self.VA):#if the variable already exists
                            var = self.VA[sourceData[segmentIndex+1][0]]
                            instruction = ("0" + var)

                            if(self.debug): print("Already exists in dictionary, represents address:", self.lastVDA)

                        else:
                            predefined = False

                            if(sourceData[segmentIndex+1][0] in PREDEFINED_SYMBOLS or sourceData[segmentIndex+1][0][0] == "R"): # if it is in predefined symbols or the first char is "R"
                                addr = ""
                                if(sourceData[segmentIndex+1][0][0] == "R"): #if its one of the rs
                                    predefined = True

                                    if(len(sourceData[segmentIndex+1][0]) == 2): #R2 single digits
                                        addr = sourceData[segmentIndex+1][0][1]
                                    elif(len(sourceData[segmentIndex+1][0]) == 3): #R15 double digits
                                        addr = sourceData[segmentIndex+1][0][1:3]
                                    else:
                                        predefined = False
                                else: #its just another predefined symbol
                                    predefined = True
                                    addr = PREDEFINED_SYMBOLS[sourceData[segmentIndex+1][0]]

                                if(self.debug): print("Variable name identified as a predefined symbol:", sourceData[segmentIndex+1][0], "->", addr)

                                if(predefined): instruction = ("0" + self.formatBinary(int(addr), width=CPU_WIDTH-1))

                            if(not predefined):

                                if(self.debug): print("Variable does not exist, adding it to the dictionary and creating an address for it... ")

                                #create the key in the dictionary
                                self.lastVDA = self.lastVDA + 1
                                if(self.debug): print("Next dictionary address is:", self.lastVDA)


                                self.VA[sourceData[segmentIndex+1][0]] = self.formatBinary(self.lastVDA, width=CPU_WIDTH-1)
                                instruction = ("0" + self.VA[sourceData[segmentIndex+1][0]])

                                if(self.debug): print("Dictionary is now:", self.VA)

                elif(sourceData[segmentIndex+1][1] == INT_DATA_IDENTIFIER):
                    instruction = ("0" + self.formatBinary(int(sourceData[segmentIndex+1][0]), width=CPU_WIDTH-1)) #width = 15 because we must reserve the first bit for a instruction identifier

            elif(sourceData[segmentIndex][1] == C_TARGET_IDENTIFIER or sourceData[segmentIndex][1] == JMP_TARGET):

                c, a, d, JMP = "000000", "0", "000", "000"

                if(sourceData[segmentIndex][1] == JMP_TARGET): #is JMP
                    if(self.debug): print("Instruction type is a jump")
                    c, a= self.getCAcode(sourceData, False)
                    JMP = self.getJMPCode(sourceData)


                else:   
                    if(self.debug): print("Instruction type is a C instruciton")
                    #we know we are dealing with a c instruction now
                    c, a= self.getCAcode(sourceData, True)
                    d = self.getDCode(sourceData)
                    
                
                instruction = "111" + a + c + d + JMP
                



        return(instruction)



#just run it all now:

assembler = Assembler()


if(__name__ == "__main__"):
    showWhatsHappening = True

    print("Opening source.asm...")

    sourceFile = open("source.asm", mode="r")
    assembled = assembler.assemble(sourceFile.readlines(), debug=showWhatsHappening)

    print("\nAssembled file:\n\n" + assembled)
    print("Writing to source.hack...")

    outFile = open("source.hack", "w")
    outFile.write(assembled)

#used:
#https://stackoverflow.com/questions/1024847/add-new-keys-to-a-dictionary