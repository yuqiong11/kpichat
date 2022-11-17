from ast import operator
from collections import deque
import re

OPERATORS = ['+','-','*','/']
SPECIAL_CHARACTERS = ['+','-','*','/','(',')']
NUMBERS = ['0','1','2','3','4','5','6','7','8','9','.']


class ConvertMathFormular():

    def __init__(self):
        # initialize two stacks
        self.operands = deque()
        self.operators = deque()


    def get_tokens(self, formular):
        # (5+21/3)*2 -> ['(','5','+','2','1','/','3',')','*','2'] -> ['(','5','+','21','/','3',')','*','2']
        tokens = list(formular)
        wanted_tokens = []
        temp = ''
        for token in tokens:
            if token in NUMBERS:                
                temp += token
            elif token in SPECIAL_CHARACTERS:
                if temp:
                    wanted_tokens.append(temp)
                    temp = ''
                    wanted_tokens.append(token)
                else:
                    wanted_tokens.append(token)

        if temp:
            wanted_tokens.append(temp)

        return wanted_tokens


    def main_func(self, tokens):
        # func that does the trick
        # algorithm:
        # loop over tokens
        # add tokens into stacks using following rules:
        # if left parenthesis, then add all tokens until right parenthesis, pop
        # if one operand has higher priority than the previous one, pop

        # ['(', '5', '+', '21', '/', '3', ')', '*', '2', '+', '5']

        print("tokens", tokens)

        skip_next_token = False

        for i in range(len(tokens)):

            if skip_next_token:
                skip_next_token = False
                continue
                
            token = tokens[i]
            # print(token)
            # loop
            if token == '(':
                # if left parenthesis, then add all tokens until right parenthesis, pop
                self.operators.append(token)

            
            elif token in OPERATORS:
                if self.operators:
                    current_operator_priority = self.check_priority(token, self.operators[-1])
                    previous_operator_priority = self.check_priority(self.operators[-1], token)
                    # print('token', token)
                    # print('priority', priority)
                    # print('self.operands', self.operands)
                    # print('########################################################')
                    if current_operator_priority:
                        # if the current operator has higher priority
                        # add one more operand and pop and calculate
                        # add the result again in operands stack
                        next_operand = tokens[i+1]
                        if next_operand == '(':
                            self.operators.append(token)
                            continue
                        previous_operand = self.operands.pop()
                        result = self.calculate(token, float(previous_operand), float(next_operand))
                        self.operands.append(result)
                        skip_next_token = True
                    elif previous_operator_priority:
                        # if the current operator has higher priority
                        previous_operator = self.operators.pop()
                        current_operand = self.operands.pop()
                        previous_operand = self.operands.pop()
                        result = self.calculate(previous_operator, float(previous_operand), float(current_operand))
                        self.operands.append(result)
                        self.operators.append(token)
                    else:
                        # equal priority
                        self.operators.append(token)
                else:
                    self.operators.append(token)

            
            elif token == ')':
                # print('hihhuhuihuih')
                # print('operands', self.operands)
                # print('operators', self.operators)

                # right parenthesis, pop
                operator_pop = True

                while operator_pop:
                    operator = self.operators.pop()
                    if operator == '(':
                        operator_pop = False
                        break
                    right_operand = self.operands.pop()
                    left_operand = self.operands.pop()

                    result = self.calculate(operator, float(left_operand), float(right_operand))
                    self.operands.append(result)

            else:
                self.operands.append(token)

        # print('wwwwwwwwwwwwwwwwwwww')
        # print('operands', self.operands)
        # print('operators', self.operators)

        # loop is over, pop all elements and calculate the result
        while self.operators:
            operator = self.operators.pop()
            right_operand = self.operands.pop()
            left_operand = self.operands.pop()
            result = self.calculate(operator, float(left_operand), float(right_operand))
            print("result", result)
            if self.operands:
                # print(self.operands)
                self.operands.append(result)

        return result

        
    def check_priority(self, new, old):
        if (new in ['*','/']) and (old in ['+','-']):
            return True
        return False


    def calculate(self, operator, operand_1, operand_2):
        if operator == '+':
            return self.add(operand_1, operand_2)
        elif operator == '-':
            return self.sub(operand_1, operand_2)
        elif operator == '*':
            return self.mul(operand_1, operand_2)
        elif operator == '/':
            return self.div(operand_1, operand_2)

    @staticmethod
    def add(x, y):
        return x+y

    @staticmethod
    def sub(x,y):
        return x-y

    @staticmethod
    def mul(x,y):
        return x*y

    @staticmethod
    def div(x,y):
        return x/y


# myformular = ['(5+21/3)*2+5','(10-5)*2+5','3+2*8-10/5','3*(2+8)-10/5']
# myformular = ['6*(4+2)-2*3', '6-(2+4)/3', '5-8/(4+2)']
# myformular = ['5-8/(4+2)', '8/2+5*(3+4)']

# mystack = ConvertMathFormular()

# for _ in myformular:
#     tokens = mystack.get_tokens(_)
#     # print(tokens)
#     result = mystack.main_func(tokens)
#     print(result)















# below not used #################################################

# class ConvertMathFormular():

#     def __init__(self):
#         # initialize two stacks
#         self.operands = deque()
#         self.operators = deque()

#     def get_tokens(self, formular):
#         # get rid of other special characters
#         # tokens = []
#         # splited_formular = re.split(r"[,.\s]\s*", formular)
#         # for ele in splited_formular:
#         #     if '@' in ele:
#         #         characters = list(ele)
#         #         for character in characters:
#         #             if character in ['+', '-', '*', '/']
#         wanted_tokens = []
        
#         tokens = list(formular)
#         for token in tokens:
#             if token in ['+', '-', '*', '/', '(', ')']:
#                 wanted_tokens.append(token)
#             elif token == '@':
#                 temp = ''
#                 temp += token
                

#     def main_func(self):
#         # func that does the trick
#         # algorithm:
#         # convert formular into tokens
#         # loop over tokens
#         # add tokens into stacks using following rules:
#         # if left parenthesis, then add all tokens until right parenthesis, pop
#         # if one operand has higher priority than the previous one, pop

#         pass

# myformular = '(@my_param + @my_param_1/@param)'
# mystack = ConvertMathFormular()
# print(mystack.get_tokens(myformular))
