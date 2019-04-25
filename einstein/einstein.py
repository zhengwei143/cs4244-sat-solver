num_hse = 5
end_token = '0'

# color
color = {"blue": 0, "green": 1, "red": 2, "white": 3, "yellow": 4}
# nationality
nationality = {"dane": 5, "brit": 6, "german": 7, "swede": 8, "norwegian": 9}
# drink
drink = {"beer": 10, "coffee": 11, "milk": 12, "tea": 13, "water": 14}
# cigarette
cigarette = {"blend": 15, "bluemaster": 16, "dunhill": 17, "pallmall": 18, "prince": 19}
# pet
pet = {"birds": 20, "cats": 21, "dogs": 22, "fish": 23, "horses": 24}

attribute_types = [color, nationality, drink, cigarette, pet]

def eval(hse, attr_type_map, attribute):
    return hse + 5*attr_type_map[attribute]

def neighbour(type1, attr1, type2, attr2):
    cnf = []
    for i in range(1, num_hse+1):
        if i == 1:
            cnf.append("-{} {} {}".format(eval(i, type1, attr1), eval(i+1, type2, attr2), end_token))
        elif i == num_hse:
            cnf.append("-{} {} {}".format(eval(i, type1, attr1), eval(i-1, type2, attr2), end_token))
        else:
            cnf.append("-{} {} {} {}".format(
                eval(i, type1, attr1), 
                eval(i-1, type2, attr2), 
                eval(i+1, type2, attr2),
                end_token))
    return '\n'.join(cnf) + '\n'

def bi_implication(type1, attr1, type2, attr2):
    cnf = []
    for i in range(1, num_hse+1):
        cnf.append("-{} {} {}".format(eval(i, type1, attr1), eval(i, type2, attr2), end_token))
        cnf.append("{} -{} {}".format(eval(i, type1, attr1), eval(i, type2, attr2), end_token))
    return '\n'.join(cnf) + '\n'

def add_assumptions():
    cnf = []
    for t in attribute_types:
        for attr in t:
            cat_cnf = []
            for i in range(1, num_hse+1):
                cat_cnf.append(str(eval(i, t, attr)))
            cat_cnf.append(end_token)
            cnf.append(' '.join(cat_cnf))

            for i in range(1, num_hse+1):
                for j in range(1, i):
                    cnf.append("-{} -{} {}".format(eval(i, t, attr), eval(j, t, attr), end_token))
                for another_attr in t:
                    if another_attr != attr:
                        cnf.append("-{} -{} {}".format(eval(i, t, attr), eval(i, t, another_attr), end_token))

    return '\n'.join(cnf) + '\n'


def generate_einstein_cnf():
    cnf_file = open("einstein.cnf", "w+")

    cnf_file.write(add_assumptions())

    # The Brit lives in the red house
    cnf_file.write(bi_implication(nationality, "brit", color, "red"))

    # The Swede keeps dogs as pets
    cnf_file.write(bi_implication(nationality, "swede", pet, "dogs"))

    # The Dane drinks tea
    cnf_file.write(bi_implication(nationality, "dane", drink, "tea"))

    # The green house is on the left of the white house
    cnf_file.write("-{} {} {} {} {} {}\n".format(eval(1, color, "green"), eval(2, color, "white"), eval(3, color, "white"), eval(4, color, "white"), eval(5, color, "white"), end_token))
    cnf_file.write("-{} {} {} {} {}\n".format(eval(2, color, "green"), eval(3, color, "white"), eval(4, color, "white"), eval(5, color, "white"), end_token))
    cnf_file.write("-{} {} {} {}\n".format(eval(3, color, "green"), eval(4, color, "white"), eval(5, color, "white"), end_token))
    cnf_file.write("-{} {} {}\n".format(eval(4, color, "green"), eval(5, color, "white"), end_token))
    cnf_file.write("-{} {}\n".format(eval(5, color, "green"),end_token))

    # The green house's owner drinks coffee
    cnf_file.write(bi_implication(drink, "coffee", color, "green"))

    # The person who smokes Pall Mall rears birds
    cnf_file.write(bi_implication(cigarette, "pallmall", pet, "birds"))

    # The owner of the yellow house smokes Dunhill
    cnf_file.write(bi_implication(color, "yellow", cigarette, "dunhill"))

    # The man living in the center house drinks milk
    cnf_file.write("{} {}\n".format(eval(3, drink, "milk"), end_token))

    # The Norwegian lives in the first house
    cnf_file.write("{} {}\n".format(eval(1, nationality, "norwegian"), end_token))

    # The man who smokes Blends lives next to the one who keeps cats
    cnf_file.write(neighbour(cigarette, "blend", pet, "cats"))

    # The man who keeps the horse lives next to the man who smokes Dunhill
    cnf_file.write(neighbour(pet, "horses", cigarette, "dunhill"))
    
    # The owner who smokes Bluemasters drinks beer
    cnf_file.write(bi_implication(cigarette, "bluemaster", drink, "beer"))

    # The German smokes Prince
    cnf_file.write(bi_implication(nationality, "german", cigarette, "prince"))

    # The Norwegian lives next to the blue house
    cnf_file.write("{} {}\n".format(eval(2, color, "blue"), end_token))

    # The man who smokes Blends has a neighbor who drinks water
    cnf_file.write(neighbour(cigarette, "blend", drink, "water"))

    cnf_file.close()

def generate_ref():
    ref_file = open("reference.txt", "w+")

    for c in ["blue", "green", "red", "white", "yellow"]:
        for i in range(1, num_hse+1):
            ref_file.write("{}: color({},{})\n".format(eval(i, color, c),i,c))

    for n in ["dane", "brit", "german", "swede", "norwegian"]:
        for i in range(1, num_hse+1):
            ref_file.write("{}: nationality({},{})\n".format(eval(i, nationality, n),i,n))

    for d in ["beer", "coffee", "milk", "tea", "water"]:
        for i in range(1, num_hse+1):
            ref_file.write("{}: drink({},{})\n".format(eval(i, drink, d),i,d))

    for cig in ["blend", "bluemaster", "dunhill", "pallmall", "prince"]:
        for i in range(1, num_hse+1):
            ref_file.write("{}: cigarette({},{})\n".format(eval(i, cigarette, cig),i,cig))

    for p in ["birds", "cats", "dogs", "fish", "horses"]:
        for i in range(1, num_hse+1):
            ref_file.write("{}: pet({},{})\n".format(eval(i, pet, p),i,p))

    ref_file.close()

generate_einstein_cnf()
generate_ref()
