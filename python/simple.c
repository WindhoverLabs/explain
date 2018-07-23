//#include <stdio.h>
//#include <stdlib.h>

// Simple typedef. easy.
typedef int potato;
typedef potato boiled;

// struct named basket assigned to typedef
// named basket. Duplicate name issue.
typedef struct basket {
    potato potate;
    boiled boil;
    potato lotsa[2];
} basket;

// Array typedef, array has no name so anything
// that refers to it will be using the debug address
// which changes per compilation unit.
typedef basket baskets[10];

typedef union lunch_box {
    potato potato;
    potato many_potatoes[2];
    potato* potential_potato;
    potato (*many_potential_potatoes)[10];
} lunch_box;

// Two identical structs create separate debug entries.
typedef struct {
    int x;
} test1;

typedef struct {
    int x;
} test2;


// Struct typedef'd to same name as struct.
typedef struct tomato {
    int x;
} tomato;

// Declare, typedef, then define struct.
struct carrot;
typedef struct carrot carrot;
struct carrot {
    int leaves;
};

// Define struct, typedef twice.
struct lettuce {
    int color;
};
typedef struct lettuce romaine;
typedef struct lettuce iceberg;


boiled add(potato x, potato y) {
    return x + y;
}

int main() {
    struct {
        int a;
        long b;
    } thing;


    basket bask;
    potato a=10, b=20;
    baskets c;
    boiled result;
    lunch_box e;
    long multi;
    test1 f;
    test2 g;
    tomato h;
    carrot i;
    romaine j;
    iceberg k;

    result = add(a, b);
    multi = result * b;
    bask.potate = a;
    bask.boil = result;
    c[0] = bask;
    return 0;
}