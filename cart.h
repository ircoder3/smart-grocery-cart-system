#ifndef CART_H
#define CART_H

typedef struct CategoryBudget {
    char name[20];
    float max_amount;
    float current_spent;
} CategoryBudget;

typedef struct Item {
    char name[50];
    float price;
    int priority;
    int quantity;
    char category[20];
    struct Item* next;
} Item;

typedef struct Cart {
    Item* head;
    float budget;
    float spent;
    int item_count;
    CategoryBudget categories[10];
    int category_count;
} Cart;

// Function declarations
Cart* create_cart(float budget);
int add_item_with_replacement(Cart* cart, const char* name, float price, 
                            int priority, int quantity, const char* category);
int remove_item_by_name(Cart* cart, const char* name);
int remove_selected_item(Cart* cart, void* item_ptr);  // NEW
void clear_cart(Cart* cart);
void free_cart(Cart* cart);

float get_cart_total(const Cart* cart);
float get_remaining_budget(const Cart* cart);
int get_item_count(const Cart* cart);

int set_category_budget(Cart* cart, const char* category_name, float max_amount);
float get_category_spent(const Cart* cart, const char* category_name);
float get_category_remaining(const Cart* cart, const char* category_name);

const char* get_cart_display(const Cart* cart);
const char* get_budget_summary(const Cart* cart);
const char* get_category_summary(const Cart* cart);

void print_cart_state(const Cart* cart);
void test_cart(void);
void debug_cart_structure(const Cart* cart);

#endif // CART_H