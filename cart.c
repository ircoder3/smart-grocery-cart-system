#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <float.h>
#include "cart.h"

#define MAX_DISPLAY_SIZE 4096
#define CATEGORY_COUNT 6
#define MAX_REMOVABLE_ITEMS 20

// Helper function to create a new item
static Item* create_item(const char* name, float price, int priority, int quantity, const char* category) {
    Item* new_item = (Item*)malloc(sizeof(Item));
    if (!new_item) return NULL;
    
    strncpy(new_item->name, name, sizeof(new_item->name) - 1);
    new_item->name[sizeof(new_item->name) - 1] = '\0';
    new_item->price = price;
    new_item->priority = priority;
    new_item->quantity = quantity;
    strncpy(new_item->category, category, sizeof(new_item->category) - 1);
    new_item->category[sizeof(new_item->category) - 1] = '\0';
    new_item->next = NULL;
    
    return new_item;
}

// Create a new cart
Cart* create_cart(float budget) {
    Cart* cart = (Cart*)malloc(sizeof(Cart));
    if (!cart) return NULL;
    
    cart->head = NULL;
    cart->budget = budget;
    cart->spent = 0.0;
    cart->item_count = 0;
    cart->category_count = CATEGORY_COUNT;
    
    // Initialize categories with zero budget
    const char* category_names[CATEGORY_COUNT] = {
        "Dairy", "Vegetables", "Snacks", "Meat", "Beverages", "Other"
    };
    
    for (int i = 0; i < CATEGORY_COUNT; i++) {
        strncpy(cart->categories[i].name, category_names[i], sizeof(cart->categories[i].name) - 1);
        cart->categories[i].name[sizeof(cart->categories[i].name) - 1] = '\0';
        cart->categories[i].max_amount = 0.0;
        cart->categories[i].current_spent = 0.0;
    }
    
    printf("[C] Cart created with budget $%.2f\n", budget);
    return cart;
}

// Find category index
static int find_category_index(const Cart* cart, const char* category_name) {
    for (int i = 0; i < cart->category_count; i++) {
        if (strcmp(cart->categories[i].name, category_name) == 0) {
            return i;
        }
    }
    return -1;
}

// Check if item can be added considering category budget STRICTLY
static int check_category_budget(Cart* cart, const char* category, float item_cost) {
    int cat_index = find_category_index(cart, category);
    if (cat_index == -1) return 1; // Category not found
    
    CategoryBudget* cat = &cart->categories[cat_index];
    if (cat->max_amount < 0.001) return 1; // No budget set = allow
    
    // Check if item fits in category budget
    if (cat->current_spent + item_cost <= cat->max_amount + 0.001) {
        return 1;
    }
    
    printf("[C] ❌ %s budget exceeded: $%.2f + $%.2f > $%.2f\n", 
           category, cat->current_spent, item_cost, cat->max_amount);
    return 0;
}

// Remove lowest priority from SAME CATEGORY ONLY
static int remove_lowest_priority_same_category(Cart* cart, int target_priority, const char* target_category) {
    Item* current = cart->head;
    Item* prev = NULL;
    Item* lowest = NULL;
    Item* lowest_prev = NULL;
    int lowest_prio = target_priority; // Start with target priority
    
    // Find lowest priority item in the same category
    while (current) {
        if (strcmp(current->category, target_category) == 0 && 
            current->priority < target_priority && 
            current->priority < lowest_prio) {
            lowest_prio = current->priority;
            lowest = current;
            lowest_prev = prev;
        }
        prev = current;
        current = current->next;
    }
    
    if (!lowest) return 0; // No lower priority items in same category
    
    // Remove the item
    float cost = lowest->price * lowest->quantity;
    
    if (lowest_prev) {
        lowest_prev->next = lowest->next;
    } else {
        cart->head = lowest->next;
    }
    
    // Update totals
    cart->spent -= cost;
    cart->item_count--;
    
    // Update category
    int cat_idx = find_category_index(cart, lowest->category);
    if (cat_idx != -1) {
        cart->categories[cat_idx].current_spent -= cost;
        if (cart->categories[cat_idx].current_spent < 0) {
            cart->categories[cat_idx].current_spent = 0;
        }
    }
    
    printf("[C] 🗑️ SAME CAT Removed: %s (P:%d, $%.2f) from %s\n", 
           lowest->name, lowest->priority, cost, target_category);
    
    free(lowest);
    return 1;
}

// Main add function with priority-based replacement - NEW LOGIC
int add_item_with_replacement(Cart* cart, const char* name, float price, int priority, int quantity, const char* category) {
    if (!cart) {
        printf("[C] Cart is NULL\n");
        return 0;
    }
    
    float item_cost = price * quantity;
    
    printf("\n[C] ========== ADD ITEM ATTEMPT ==========\n");
    printf("[C] Item: %s\n", name);
    printf("[C] Price: $%.2f x %d = $%.2f\n", price, quantity, item_cost);
    printf("[C] Priority: %d\n", priority);
    printf("[C] Category: %s\n", category);
    printf("[C] Current spent: $%.2f / $%.2f\n", cart->spent, cart->budget);
    printf("[C] Items in cart: %d\n", cart->item_count);
    
    // 1. First check overall budget
    if (cart->spent + item_cost > cart->budget + 0.001) {
        printf("[C] ❌ Overall budget exceeded: $%.2f + $%.2f > $%.2f\n",
               cart->spent, item_cost, cart->budget);
        return 0;
    }
    
    // 2. Check category budget STRICTLY
    if (!check_category_budget(cart, category, item_cost)) {
        printf("[C] → Category budget exceeded! Trying SAME CATEGORY removal first...\n");
        
        // Remove from same category only
        int same_cat_removals = 0;
        while (!check_category_budget(cart, category, item_cost) && same_cat_removals < 10) {
            if (remove_lowest_priority_same_category(cart, priority, category)) {
                same_cat_removals++;
            } else {
                printf("[C] → No more lower priority items in %s category\n", category);
                break;
            }
        }
        
        // 3. Still over category budget? Check if we made space
        if (!check_category_budget(cart, category, item_cost)) {
            printf("[C] 💡 %s still over budget after same-category removal!\n", category);
            printf("[C] 👆 Return code 2 = Show user removal options\n");
            return 2;  // SIGNAL: Show UI options to user
        }
    }
    
    // 4. ADD ITEM (passed all checks)
    Item* new_item = create_item(name, price, priority, quantity, category);
    if (!new_item) {
        printf("[C] ❌ Failed to create item\n");
        return 0;
    }
    
    // Add to front of list
    // FIX: Add to END of list and properly link
if (cart->head == NULL) {
    // First item
    cart->head = new_item;
} else {
    // Find the last item
    Item* last = cart->head;
    while (last->next != NULL) {
        last = last->next;
    }
    // Link new item after the last one
    last->next = new_item;
}

printf("[C] After adding: cart->head=%p, cart->head->next=%p\n", 
       (void*)cart->head, (void*)(cart->head ? cart->head->next : NULL));
    
    // Update totals
    cart->spent += item_cost;
    cart->item_count++;
    
    // Update category
    int cat_idx = find_category_index(cart, category);
    if (cat_idx != -1) {
        cart->categories[cat_idx].current_spent += item_cost;
    }
    
    printf("[C] ✅ %s added successfully!\n", name);
    printf("[C] New total: $%.2f, Items: %d\n", cart->spent, cart->item_count);
    printf("[C] ======================================\n");
    
    return 1;
}

// Remove item by name
int remove_item_by_name(Cart* cart, const char* name) {
    if (!cart || !cart->head) {
        printf("[C] Cannot remove: cart is empty or NULL\n");
        return 0;
    }
    
    Item* current = cart->head;
    Item* prev = NULL;
    
    while (current && strcmp(current->name, name) != 0) {
        prev = current;
        current = current->next;
    }
    
    if (!current) {
        printf("[C] Item '%s' not found\n", name);
        return 0;
    }
    
    // Remove item
    float removed_cost = current->price * current->quantity;
    
    if (prev) {
        prev->next = current->next;
    } else {
        cart->head = current->next;
    }
    
    cart->spent -= removed_cost;
    cart->item_count--;
    
    // Update category
    int cat_index = find_category_index(cart, current->category);
    if (cat_index != -1) {
        cart->categories[cat_index].current_spent -= removed_cost;
        if (cart->categories[cat_index].current_spent < 0) {
            cart->categories[cat_index].current_spent = 0;
        }
    }
    
    printf("[C] Removed item: %s ($%.2f)\n", name, removed_cost);
    printf("[C] New total: $%.2f, Items: %d\n", cart->spent, cart->item_count);
    
    free(current);
    return 1;
}

// Get cart total
float get_cart_total(const Cart* cart) {
    if (!cart) {
        printf("[C] get_cart_total: cart is NULL\n");
        return 0.0;
    }
    return cart->spent;
}

// Get remaining budget
float get_remaining_budget(const Cart* cart) {
    if (!cart) {
        printf("[C] get_remaining_budget: cart is NULL\n");
        return 0.0;
    }
    float remaining = cart->budget - cart->spent;
    return remaining > 0 ? remaining : 0.0;
}

// Get item count
int get_item_count(const Cart* cart) {
    if (!cart) {
        printf("[C] get_item_count: cart is NULL\n");
        return 0;
    }
    return cart->item_count;
}

// Set category budget
int set_category_budget(Cart* cart, const char* category_name, float max_amount) {
    if (!cart) return 0;
    
    int cat_index = find_category_index(cart, category_name);
    if (cat_index == -1) return 0;
    
    cart->categories[cat_index].max_amount = max_amount;
    printf("[C] Set budget for %s: $%.2f\n", category_name, max_amount);
    return 1;
}

// Get category spent
float get_category_spent(const Cart* cart, const char* category_name) {
    if (!cart) return 0.0;
    
    int cat_index = find_category_index(cart, category_name);
    if (cat_index == -1) return 0.0;
    
    float spent = cart->categories[cat_index].current_spent;
    return spent;
}

// Get category remaining
float get_category_remaining(const Cart* cart, const char* category_name) {
    if (!cart) return 0.0;
    
    int cat_index = find_category_index(cart, category_name);
    if (cat_index == -1) return 0.0;
    
    float remaining = cart->categories[cat_index].max_amount - 
                     cart->categories[cat_index].current_spent;
    return remaining > 0 ? remaining : 0.0;
}

const char* get_cart_display(const Cart* cart) {
    static char buffer[MAX_DISPLAY_SIZE];
    memset(buffer, 0, MAX_DISPLAY_SIZE);
    
    if (!cart || !cart->head) {
        strcpy(buffer, "🛒 Cart is empty!");
        return buffer;
    }
    
    // SIMPLE: Just print like print_cart_state does
    char* ptr = buffer;
    int remaining = MAX_DISPLAY_SIZE;
    
    // Header
    int written = snprintf(ptr, remaining, 
        "========================================\n"
        "            🛒 SHOPPING CART           \n"
        "========================================\n\n");
    ptr += written;
    remaining -= written;
    
    // Items
    Item* current = cart->head;
    int item_num = 1;
    
    while (current && remaining > 100) {
        float item_total = current->price * current->quantity;
        
        written = snprintf(ptr, remaining,
            "%d. %s\n"
            "   $%.2f × %d = $%.2f\n"
            "   [Category: %s, Priority: %d]\n\n",
            item_num, current->name, current->price,
            current->quantity, item_total,
            current->category, current->priority);
        
        ptr += written;
        remaining -= written;
        
        current = current->next;
        item_num++;
    }
    
    // Footer
    snprintf(ptr, remaining,
        "========================================\n"
        "Total:      $%.2f\n"
        "Items:      %d\n"
        "Budget:     $%.2f\n"
        "Remaining:  $%.2f\n"
        "========================================\n",
        cart->spent, cart->item_count, cart->budget,
        cart->budget - cart->spent);
    
    printf("[C] get_cart_display: wrote %d items\n", item_num - 1);
    
    return buffer;
}
// Get budget summary
const char* get_budget_summary(const Cart* cart) {
    static char buffer[1024];
    
    if (!cart) {
        strcpy(buffer, "Cart is NULL");
        return buffer;
    }
    
    float remaining = cart->budget - cart->spent;
    float usage = (cart->budget > 0) ? (cart->spent / cart->budget) * 100 : 0;
    
    snprintf(buffer, sizeof(buffer),
            "========================================\n"
            "            💰 BUDGET SUMMARY           \n"
            "========================================\n"
            "Total Budget:      $%10.2f\n"
            "Amount Spent:      $%10.2f\n"
            "Remaining:         $%10.2f\n"
            "Usage:             %11.1f%%\n"
            "Items in Cart:     %11d\n"
            "========================================\n",
            cart->budget, cart->spent, remaining, 
            usage, cart->item_count);
    
    return buffer;
}

// Get category summary
const char* get_category_summary(const Cart* cart) {
    static char buffer[2048];
    
    if (!cart) {
        strcpy(buffer, "Cart is NULL");
        return buffer;
    }
    
    buffer[0] = '\0';
    char temp[256];
    
    strcpy(buffer, "========================================\n");
    strcat(buffer, "        📊 CATEGORY BUDGETS        \n");
    strcat(buffer, "========================================\n\n");
    
    float total_budget = 0;
    float total_spent = 0;
    
    for (int i = 0; i < cart->category_count; i++) {
        const CategoryBudget* cat = &cart->categories[i];
        float remaining = cat->max_amount - cat->current_spent;
        if (remaining < 0) remaining = 0;
        float usage = (cat->max_amount > 0.001) ? (cat->current_spent / cat->max_amount) * 100 : 0;
        
        snprintf(temp, sizeof(temp),
                "%-12s $%8.2f / $%8.2f  Remaining: $%8.2f  (%5.1f%%)\n",
                cat->name, cat->current_spent, cat->max_amount, 
                remaining, usage);
        strcat(buffer, temp);
        
        total_budget += cat->max_amount;
        total_spent += cat->current_spent;
    }
    
    strcat(buffer, "\n");
    strcat(buffer, "========================================\n");
    snprintf(temp, sizeof(temp),
            "TOTAL:      $%8.2f / $%8.2f  Remaining: $%8.2f\n",
            total_spent, total_budget, total_budget - total_spent);
    strcat(buffer, temp);
    strcat(buffer, "========================================\n");
    
    return buffer;
}

// Clear cart
void clear_cart(Cart* cart) {
    if (!cart) return;
    
    Item* current = cart->head;
    while (current) {
        Item* temp = current;
        current = current->next;
        free(temp);
    }
    
    cart->head = NULL;
    cart->spent = 0.0;
    cart->item_count = 0;
    
    for (int i = 0; i < cart->category_count; i++) {
        cart->categories[i].current_spent = 0.0;
    }
    
    printf("[C] Cart cleared\n");
}

// Free cart
void free_cart(Cart* cart) {
    if (!cart) return;
    clear_cart(cart);
    free(cart);
    printf("[C] Cart freed from memory\n");
}

// Print cart state for debugging
void print_cart_state(const Cart* cart) {
    if (!cart) {
        printf("[CART STATE] Cart is NULL\n");
        return;
    }
    
    printf("\n========== CART STATE ==========\n");
    printf("Budget: $%.2f\n", cart->budget);
    printf("Spent:  $%.2f\n", cart->spent);
    printf("Remaining: $%.2f\n", cart->budget - cart->spent);
    printf("Items: %d\n", cart->item_count);
    
    if (cart->head) {
        printf("\nItems (Priority order):\n");
        Item* current = cart->head;
        int i = 1;
        while (current) {
            printf("%d. %-15s $%.2f x %d = $%.2f [P:%d, Cat:%s]\n",
                   i, current->name, current->price, current->quantity,
                   current->price * current->quantity,
                   current->priority, current->category);
            current = current->next;
            i++;
        }
    } else {
        printf("\nCart is empty\n");
    }
    
    printf("\nCategory Budgets:\n");
    for (int i = 0; i < cart->category_count; i++) {
        printf("  %-12s: $%.2f / $%.2f\n", 
               cart->categories[i].name,
               cart->categories[i].current_spent,
               cart->categories[i].max_amount);
    }
    
    printf("================================\n");
}

// Test function
void test_cart() {
    printf("\n========== CART TEST ==========\n");
    
    Cart* cart = create_cart(30.0);
    
    printf("\n1. Adding: Milk ($3.50, priority 8, Dairy)\n");
    add_item_with_replacement(cart, "Milk", 3.50, 8, 1, "Dairy");
    print_cart_state(cart);
    
    printf("\n2. Adding: Bread ($2.99, priority 5, Other)\n");
    add_item_with_replacement(cart, "Bread", 2.99, 5, 1, "Other");
    print_cart_state(cart);
    
    printf("\n3. Adding: Eggs ($4.00, priority 7, Dairy)\n");
    add_item_with_replacement(cart, "Eggs", 4.00, 7, 1, "Dairy");
    print_cart_state(cart);
    
    printf("\n4. Setting Dairy budget to $5.00\n");
    set_category_budget(cart, "Dairy", 5.00);
    
    printf("\n5. Trying to add Cheese ($3.00, priority 6, Dairy)\n");
    printf("This should trigger category budget warning\n");
    int result = add_item_with_replacement(cart, "Cheese", 3.00, 6, 1, "Dairy");
    printf("Result code: %d\n", result);
    
    free_cart(cart);
    printf("\n========== TEST COMPLETE ==========\n");
}
void debug_cart_structure(const Cart* cart) {
    if (!cart) {
        printf("[DEBUG] Cart is NULL\n");
        return;
    }
    
    printf("\n========== CART STRUCTURE DEBUG ==========\n");
    printf("Item count: %d\n", cart->item_count);
    printf("Head pointer: %p\n", (void*)cart->head);
    
    Item* current = cart->head;
    int i = 1;
    
    while (current) {
        printf("Item %d at %p:\n", i, (void*)current);
        printf("  Name: %s\n", current->name);
        printf("  Next: %p\n", (void*)current->next);
        printf("  Price: $%.2f, Qty: %d\n", current->price, current->quantity);
        printf("  Priority: %d, Category: %s\n", current->priority, current->category);
        
        current = current->next;
        i++;
    }
    
    if (i == 1) {
        printf("No items in list (but count says %d)\n", cart->item_count);
    }
    
    printf("========== END DEBUG ==========\n");
}
