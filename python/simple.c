#include <stdio.h>
#include <string.h>
//#include <stdlib.h>

void printByte(char byte) {
    char mask = 0x80;
    for(int i=0; i<8; ++i){
        // print last bit and shift left.
        printf("%u", byte & mask ? 1 : 0);
        byte = byte << 1;
    }
    printf(" ");
}

void printBytes(char* address, int numBits) {
    for (int i=0; i < numBits; i++) {
        printByte(address[i]);
    }
    printf("\n");
}

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
typedef basket baskets2[10];

typedef union lunch_box {
    potato potato;
    potato array_potatoes[2];
    potato* potential_potato;
    potato (*p_array_potatoes)[10];
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

// Struct typedef'd to different name as struct.
typedef struct aubergine {
    int x;
} eggplant;

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

// Bit Fields
#pragma pack(1)
typedef struct partial {
//    char a;
//    char b: 5;
//    short c: 10;
//    char d: 4;
    char a: 1;
    char b: 2;
    char c: 5;
    short d: 10;
} partial;


typedef union punion {
    short s;
    short u: 4;
} punion;


int main() {
    eggplant e = {4};

    return 0;
}