#cart_wrapper.py
import ctypes
import os
import io
import sys
import logging

logger = logging.getLogger("grocery_cart")

# Max entries fetched by get_removable_items in one call; matches the
# arrays sized in cart.c/cart.h.
MAX_REMOVABLE_ITEMS = 20


class CartWrapper:
    def __init__(self):
        # Load C library
        if os.name == 'nt':  # Windows
            lib_path = './cart.dll'
        else:  # Linux/Mac
            lib_path = './libcart.so'

        logger.debug("Loading C library from: %s", os.path.abspath(lib_path))

        try:
            self.lib = ctypes.CDLL(lib_path)
        except OSError as e:
            # Fall back to an absolute path in case the working directory
            # isn't where the .so/.dll lives (e.g. Streamlit launched
            # elsewhere).
            try:
                self.lib = ctypes.CDLL(os.path.abspath(lib_path))
            except OSError:
                raise ImportError(
                    f"Cannot load C library '{lib_path}'. Build it first with:\n"
                    f"  gcc -shared -fPIC -o libcart.so cart.c   (Linux/Mac)\n"
                    f"  gcc -shared -o cart.dll cart.c           (Windows)\n"
                    f"Original error: {e}"
                ) from e

        # Define function prototypes
        self.setup_functions()

        # Cart pointer
        self.cart_ptr = None
    
    def setup_functions(self):
        # create_cart
        self.lib.create_cart.argtypes = [ctypes.c_float]
        self.lib.create_cart.restype = ctypes.c_void_p
        
        # add_item_with_replacement
        self.lib.add_item_with_replacement.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_float,
            ctypes.c_int,
            ctypes.c_int,
            ctypes.c_char_p
        ]
        self.lib.add_item_with_replacement.restype = ctypes.c_int
        
        # remove_item_by_name
        self.lib.remove_item_by_name.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p
        ]
        self.lib.remove_item_by_name.restype = ctypes.c_int

        # remove_selected_item
        self.lib.remove_selected_item.argtypes = [
            ctypes.c_void_p,
            ctypes.c_void_p
        ]
        self.lib.remove_selected_item.restype = ctypes.c_int

        # get_removable_items(cart, target_priority,
        #                      names[][50], costs[], priorities[], categories[][20],
        #                      max_items) -> count
        self.lib.get_removable_items.argtypes = [
            ctypes.c_void_p,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_char * 50 * MAX_REMOVABLE_ITEMS),
            ctypes.POINTER(ctypes.c_float * MAX_REMOVABLE_ITEMS),
            ctypes.POINTER(ctypes.c_int * MAX_REMOVABLE_ITEMS),
            ctypes.POINTER(ctypes.c_char * 20 * MAX_REMOVABLE_ITEMS),
            ctypes.c_int
        ]
        self.lib.get_removable_items.restype = ctypes.c_int
        
        # get_cart_display - returns const char*
        self.lib.get_cart_display.argtypes = [ctypes.c_void_p]
        self.lib.get_cart_display.restype = ctypes.c_char_p
        
        # get_budget_summary
        self.lib.get_budget_summary.argtypes = [ctypes.c_void_p]
        self.lib.get_budget_summary.restype = ctypes.c_char_p
        
        # get_category_summary
        self.lib.get_category_summary.argtypes = [ctypes.c_void_p]
        self.lib.get_category_summary.restype = ctypes.c_char_p
        
        # get_cart_total
        self.lib.get_cart_total.argtypes = [ctypes.c_void_p]
        self.lib.get_cart_total.restype = ctypes.c_float
        
        # get_remaining_budget
        self.lib.get_remaining_budget.argtypes = [ctypes.c_void_p]
        self.lib.get_remaining_budget.restype = ctypes.c_float
        
        # get_item_count
        self.lib.get_item_count.argtypes = [ctypes.c_void_p]
        self.lib.get_item_count.restype = ctypes.c_int
        
        # set_category_budget
        self.lib.set_category_budget.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p,
            ctypes.c_float
        ]
        self.lib.set_category_budget.restype = ctypes.c_int
        
        # get_category_spent
        self.lib.get_category_spent.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p
        ]
        self.lib.get_category_spent.restype = ctypes.c_float
        
        # get_category_remaining
        self.lib.get_category_remaining.argtypes = [
            ctypes.c_void_p,
            ctypes.c_char_p
        ]
        self.lib.get_category_remaining.restype = ctypes.c_float
        
        # print_cart_state
        try:
            self.lib.print_cart_state.argtypes = [ctypes.c_void_p]
            self.lib.print_cart_state.restype = None
        except:
            logger.debug("[Python] print_cart_state not found")
        
        # test_cart
        try:
            self.lib.test_cart.argtypes = []
            self.lib.test_cart.restype = None
        except:
            logger.debug("[Python] test_cart not found")
        
        # free_cart
        try:
            self.lib.free_cart.argtypes = [ctypes.c_void_p]
            self.lib.free_cart.restype = None
        except:
            logger.debug("[Python] free_cart not found")
    
    def create_cart(self, budget):
        """Create a new shopping cart"""
        logger.debug(f"[Python] Creating cart with budget: ${budget}")
        self.cart_ptr = self.lib.create_cart(ctypes.c_float(budget))
        logger.debug(f"[Python] Cart pointer: {self.cart_ptr}")
        return self.cart_ptr is not None
    
    def add_item(self, name, price, priority, quantity, category="Other"):
        """Add item to cart"""
        if not self.cart_ptr:
            logger.debug("[Python] ERROR: Cart not created! Call create_cart() first.")
            return False
        
        logger.debug(f"[Python] ======= ATTEMPTING TO ADD ITEM =======")
        logger.debug(f"[Python] Item: {name}")
        logger.debug(f"[Python] Price: ${price}")
        logger.debug(f"[Python] Priority: {priority}")
        logger.debug(f"[Python] Quantity: {quantity}")
        logger.debug(f"[Python] Category: {category}")
        logger.debug(f"[Python] Cart pointer: {self.cart_ptr}")
        
        try:
            result = self.lib.add_item_with_replacement(
                self.cart_ptr,
                name.encode('utf-8'),
                ctypes.c_float(price),
                ctypes.c_int(priority),
                ctypes.c_int(quantity),
                category.encode('utf-8')
            )
            
            logger.debug(f"[Python] C function returned: {result}")
            
            if result == 1:  # SUCCESS
                logger.debug(f"[Python] ✅ SUCCESS: Item '{name}' added to cart")
                # Get updated cart info
                item_count = self.get_item_count()
                total = self.get_total()
                logger.debug(f"[Python] Updated cart: {item_count} items, total: ${total:.2f}")
                return True
            elif result == 2:  # USER CONFIRMATION NEEDED
                logger.debug(f"[Python] ⚠️ NEEDS USER CONFIRMATION: Category budget exceeded for '{name}'")
                return 2
            else:
                logger.debug(f"[Python] ❌ FAILED: Could not add item '{name}'")
                return False
                
        except Exception as e:
            logger.debug(f"[Python] ERROR in add_item: {e}")
            import traceback
            logger.debug(f"[Python] Traceback: {traceback.format_exc()}")
            return False
    
    def remove_item(self, name):
        """Remove item by name"""
        if not self.cart_ptr:
            logger.debug("[Python] ERROR: Cart not created!")
            return False
        
        logger.debug(f"[Python] Attempting to remove item: {name}")
        
        try:
            result = self.lib.remove_item_by_name(
                self.cart_ptr,
                name.encode('utf-8')
            )
            
            logger.debug(f"[Python] Remove result: {result}")
            return bool(result)
        except Exception as e:
            logger.debug(f"[Python] ERROR in remove_item: {e}")
            return False
    
    def get_display(self):
        """Get cart display - FIXED VERSION"""
        if not self.cart_ptr:
            return "Cart not created"
    
        try:
            # Call C function - returns c_char_p → Python bytes
            result = self.lib.get_cart_display(self.cart_ptr)
        
            if not result:  # NULL pointer
                logger.debug("[Python] get_cart_display returned NULL")
                return "Cart is empty (NULL from C)"
        
            # result is already bytes containing the string
            logger.debug("[DEBUG] Raw bytes from get_cart_display (first 200):")
            logger.debug(repr(result[:200]))
            logger.debug("[DEBUG] Bytes length: %d", len(result))
        
            # Decode safely
            display = result.decode('utf-8', errors='replace')
        
            # Remove any trailing nulls (though unlikely)
            display = display.rstrip('\x00').strip()
        
            logger.debug("[DEBUG] Decoded length: %d", len(display))
            if len(display) < 20:
                logger.debug("[DEBUG] Decoded too short → fallback")
                return self.get_simple_display()
        
            logger.debug("[DEBUG] First 100 chars of display:")
            logger.debug(repr(display[:100]))
        
            return display
    
        except Exception as e:
            logger.debug("[Python] Display error: %s", e, exc_info=True)
            return self.get_simple_display()
    
    def get_simple_display(self):
        """Simple fallback display without complex memory handling"""
        if not self.cart_ptr:
            return "Cart not created"
        
        try:
            # Get basic info
            count = self.get_item_count()
            total = self.get_total()
            remaining = self.get_remaining()
            
            if count == 0:
                return "🛒 Cart is empty!"
            
            # Create simple display
            display = f"Cart Summary:\n"
            display += f"Items: {count}\n"
            display += f"Total: ${total:.2f}\n"
            display += f"Budget: ${total + remaining:.2f}\n"
            display += f"Remaining: ${remaining:.2f}\n\n"
            
            return display
        except:
            return "Error getting cart display"
    
    def get_summary(self):
        """Get budget summary"""
        if not self.cart_ptr:
            return "Cart not created"
        
        try:
            result = self.lib.get_budget_summary(self.cart_ptr)
            if result:
                return ctypes.string_at(result).decode('utf-8', errors='ignore')
            return "No summary"
        except:
            return "Error getting summary"
    
    def get_category_summary(self):
        """Get category budget summary"""
        if not self.cart_ptr:
            return "Cart not created"
        
        try:
            result = self.lib.get_category_summary(self.cart_ptr)
            if result:
                return ctypes.string_at(result).decode('utf-8', errors='ignore')
            return "No category summary"
        except:
            return "Error getting category summary"
    
    def get_total(self):
        if not self.cart_ptr:
            logger.debug("[Python] WARNING: Cart not created for get_total()")
            return 0.0
        
        try:
            result = self.lib.get_cart_total(self.cart_ptr)
            # Format to 2 decimal places
            formatted_result = round(float(result), 2)
            logger.debug(f"[Python] Total from C: ${formatted_result:.2f}")
            return formatted_result
        except Exception as e:
            logger.debug(f"[Python] Error in get_total: {e}")
            return 0.0
    
    def get_remaining(self):
        """Get remaining budget"""
        if not self.cart_ptr:
            return 0.0
        
        try:
            result = self.lib.get_remaining_budget(self.cart_ptr)
            logger.debug(f"[Python] get_remaining() returned: ${result:.2f}")
            return float(result)
        except Exception as e:
            logger.debug(f"[Python] Error in get_remaining: {e}")
            return 0.0
    
    def get_item_count(self):
        """Get number of items"""
        if not self.cart_ptr:
            logger.debug("[Python] WARNING: Cart not created for get_item_count()")
            return 0
        
        try:
            result = self.lib.get_item_count(self.cart_ptr)
            logger.debug(f"[Python] get_item_count() returned: {result}")
            return int(result)
        except Exception as e:
            logger.debug(f"[Python] Error in get_item_count: {e}")
            return 0
    
    def set_category_budget(self, category_name, max_amount):
        """Set budget for a category"""
        if not self.cart_ptr:
            logger.debug("[Python] ERROR: Cart not created!")
            return False
        
        logger.debug(f"[Python] Setting category budget: {category_name} = ${max_amount}")
        
        try:
            result = self.lib.set_category_budget(
                self.cart_ptr,
                category_name.encode('utf-8'),
                ctypes.c_float(max_amount)
            )
            logger.debug(f"[Python] set_category_budget result: {result}")
            return bool(result)
        except Exception as e:
            logger.debug(f"[Python] Error in set_category_budget: {e}")
            return False
    
    def get_category_spent(self, category_name):
        """Get amount spent in a category"""
        if not self.cart_ptr:
            return 0.0
        
        try:
            result = self.lib.get_category_spent(
                self.cart_ptr,
                category_name.encode('utf-8')
            )
            logger.debug(f"[Python] get_category_spent({category_name}) = ${result:.2f}")
            return float(result)
        except Exception as e:
            logger.debug(f"[Python] Error in get_category_spent: {e}")
            return 0.0
    
    def get_category_remaining(self, category_name):
        """Get remaining budget for a category"""
        if not self.cart_ptr:
            return 0.0
        
        try:
            result = self.lib.get_category_remaining(
                self.cart_ptr,
                category_name.encode('utf-8')
            )
            logger.debug(f"[Python] get_category_remaining({category_name}) = ${result:.2f}")
            return float(result)
        except Exception as e:
            logger.debug(f"[Python] Error in get_category_remaining: {e}")
            return 0.0
    
    def print_state(self):
        """Print cart state for debugging"""
        if not self.cart_ptr:
            logger.debug("[Python] Cart not created")
            return "Cart not created"
        
        try:
            if hasattr(self.lib, 'print_cart_state'):
                logger.debug("[Python] ===== PRINTING CART STATE TO CONSOLE =====")
                self.lib.print_cart_state(self.cart_ptr)
                logger.debug("[Python] ===== END CART STATE =====")
                return "State printed to console"
        except Exception as e:
            logger.debug(f"[Python] Error in print_state: {e}")
        return "Function not available"
    
    def get_display_working(self):
        """Use print_cart_state output - FIXED METHOD"""
        if not self.cart_ptr:
            return "Cart not created"
        
        try:
            if not hasattr(self.lib, 'print_cart_state'):
                return "Display function not available"
            
            # Redirect stdout
            old_stdout = sys.stdout
            sys.stdout = io.StringIO()
            
            # Call the working function
            self.lib.print_cart_state(self.cart_ptr)
            
            # Get output
            output = sys.stdout.getvalue()
            
            # Restore stdout
            sys.stdout = old_stdout
            
            return output
            
        except Exception as e:
            logger.debug(f"[Python] Error in get_display_working: {e}")
            # Fallback to simple display
            return self.get_simple_display()
    
    def debug_print(self):
        """Alias for print_state"""
        return self.print_state()
    
    def test(self):
        """Test the C library"""
        try:
            if hasattr(self.lib, 'test_cart'):
                logger.debug("[Python] ===== RUNNING C LIBRARY TEST =====")
                self.lib.test_cart()
                logger.debug("[Python] ===== TEST COMPLETE =====")
                return True
        except Exception as e:
            logger.debug(f"[Python] Error in test: {e}")
        return False
    
    def cleanup(self):
        """Free cart memory"""
        if self.cart_ptr:
            try:
                if hasattr(self.lib, 'free_cart'):
                    logger.debug("[Python] Freeing cart memory...")
                    self.lib.free_cart(self.cart_ptr)
                    logger.debug("[Python] Cart memory freed")
            except Exception as e:
                logger.debug(f"[Python] Error in cleanup: {e}")
            self.cart_ptr = None
    
    def get_removable_items(self, target_priority):
        """Return items currently in the cart with priority lower than
        target_priority, as a list of dicts (name, cost, priority, category)
        the UI can render and let the user pick from. Pass the chosen
        item's 'name' to remove_selected_item() to remove it.
        """
        if not self.cart_ptr:
            return []

        names = (ctypes.c_char * 50 * MAX_REMOVABLE_ITEMS)()
        costs = (ctypes.c_float * MAX_REMOVABLE_ITEMS)()
        priorities = (ctypes.c_int * MAX_REMOVABLE_ITEMS)()
        categories = (ctypes.c_char * 20 * MAX_REMOVABLE_ITEMS)()

        try:
            count = self.lib.get_removable_items(
                self.cart_ptr,
                ctypes.c_int(target_priority),
                ctypes.byref(names),
                ctypes.byref(costs),
                ctypes.byref(priorities),
                ctypes.byref(categories),
                MAX_REMOVABLE_ITEMS
            )
        except Exception as e:
            logger.warning("get_removable_items failed: %s", e)
            return []

        items = []
        for i in range(count):
            items.append({
                'name': bytes(names[i]).split(b'\x00', 1)[0].decode('utf-8', errors='replace'),
                'cost': float(costs[i]),
                'priority': int(priorities[i]),
                'category': bytes(categories[i]).split(b'\x00', 1)[0].decode('utf-8', errors='replace'),
            })
        return items

    def remove_selected_item(self, name):
        """Remove one item by name (used when the user picks from the
        removable-items list). Uses the same name-based removal as
        remove_item() under the hood — the C-side pointer identity API
        (remove_selected_item in cart.c) isn't safely exposed across the
        ctypes boundary since linked-list nodes can be freed/reused between
        calls, so name lookup is the robust path from Python.
        """
        return self.remove_item(name)