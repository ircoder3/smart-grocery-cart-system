import ctypes
import os
import sys
import io

class CartWrapper:
    def __init__(self):
        # Load C library
        if os.name == 'nt':  # Windows
            lib_path = './cart.dll'
        else:  # Linux/Mac
            lib_path = './libcart.so'
            
        print(f"[Python] Loading C library from: {os.path.abspath(lib_path)}")
        
        # Try to load
        try:
            self.lib = ctypes.CDLL(lib_path)
            print("[Python] C library loaded successfully!")
        except Exception as e:
            print(f"[Python] Error loading C library: {e}")
            # Try current directory
            try:
                self.lib = ctypes.CDLL(os.path.abspath(lib_path))
                print("[Python] Loaded from absolute path")
            except:
                raise ImportError(f"Cannot load C library: {e}")
        
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
            print("[Python] print_cart_state not found")
        
        # test_cart
        try:
            self.lib.test_cart.argtypes = []
            self.lib.test_cart.restype = None
        except:
            print("[Python] test_cart not found")
        
        # free_cart
        try:
            self.lib.free_cart.argtypes = [ctypes.c_void_p]
            self.lib.free_cart.restype = None
        except:
            print("[Python] free_cart not found")
    
    def create_cart(self, budget):
        """Create a new shopping cart"""
        print(f"[Python] Creating cart with budget: ${budget}")
        self.cart_ptr = self.lib.create_cart(ctypes.c_float(budget))
        print(f"[Python] Cart pointer: {self.cart_ptr}")
        return self.cart_ptr is not None
    
    def add_item(self, name, price, priority, quantity, category="Other"):
        """Add item to cart"""
        if not self.cart_ptr:
            print("[Python] ERROR: Cart not created! Call create_cart() first.")
            return False
        
        print(f"[Python] ======= ATTEMPTING TO ADD ITEM =======")
        print(f"[Python] Item: {name}")
        print(f"[Python] Price: ${price}")
        print(f"[Python] Priority: {priority}")
        print(f"[Python] Quantity: {quantity}")
        print(f"[Python] Category: {category}")
        print(f"[Python] Cart pointer: {self.cart_ptr}")
        
        try:
            result = self.lib.add_item_with_replacement(
                self.cart_ptr,
                name.encode('utf-8'),
                ctypes.c_float(price),
                ctypes.c_int(priority),
                ctypes.c_int(quantity),
                category.encode('utf-8')
            )
            
            print(f"[Python] C function returned: {result}")
            
            if result == 1:  # SUCCESS
                print(f"[Python] ✅ SUCCESS: Item '{name}' added to cart")
                # Get updated cart info
                item_count = self.get_item_count()
                total = self.get_total()
                print(f"[Python] Updated cart: {item_count} items, total: ${total:.2f}")
                return True
            elif result == 2:  # USER CONFIRMATION NEEDED
                print(f"[Python] ⚠️ NEEDS USER CONFIRMATION: Category budget exceeded for '{name}'")
                return 2
            else:
                print(f"[Python] ❌ FAILED: Could not add item '{name}'")
                return False
                
        except Exception as e:
            print(f"[Python] ERROR in add_item: {e}")
            import traceback
            print(f"[Python] Traceback: {traceback.format_exc()}")
            return False
    
    def remove_item(self, name):
        """Remove item by name"""
        if not self.cart_ptr:
            print("[Python] ERROR: Cart not created!")
            return False
        
        print(f"[Python] Attempting to remove item: {name}")
        
        try:
            result = self.lib.remove_item_by_name(
                self.cart_ptr,
                name.encode('utf-8')
            )
            
            print(f"[Python] Remove result: {result}")
            return bool(result)
        except Exception as e:
            print(f"[Python] ERROR in remove_item: {e}")
            return False
    
    def get_display(self):
        """Get cart display - FIXED VERSION"""
        if not self.cart_ptr:
            return "Cart not created"
    
        try:
            # Call C function - returns c_char_p → Python bytes
            result = self.lib.get_cart_display(self.cart_ptr)
        
            if not result:  # NULL pointer
                print("[Python] get_cart_display returned NULL")
                return "Cart is empty (NULL from C)"
        
            # result is already bytes containing the string
            print("[DEBUG] Raw bytes from get_cart_display (first 200):")
            print(repr(result[:200]))
            print("[DEBUG] Bytes length:", len(result))
        
            # Decode safely
            display = result.decode('utf-8', errors='replace')
        
            # Remove any trailing nulls (though unlikely)
            display = display.rstrip('\x00').strip()
        
            print("[DEBUG] Decoded length:", len(display))
            if len(display) < 20:
                print("[DEBUG] Decoded too short → fallback")
                return self.get_simple_display()
        
            print("[DEBUG] First 100 chars of display:")
            print(repr(display[:100]))
        
            return display
    
        except Exception as e:
            print(f"[Python] Display error: {e}")
            import traceback
            print(traceback.format_exc())
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
            print("[Python] WARNING: Cart not created for get_total()")
            return 0.0
        
        try:
            result = self.lib.get_cart_total(self.cart_ptr)
            # Format to 2 decimal places
            formatted_result = round(float(result), 2)
            print(f"[Python] Total from C: ${formatted_result:.2f}")
            return formatted_result
        except Exception as e:
            print(f"[Python] Error in get_total: {e}")
            return 0.0
    
    def get_remaining(self):
        """Get remaining budget"""
        if not self.cart_ptr:
            return 0.0
        
        try:
            result = self.lib.get_remaining_budget(self.cart_ptr)
            print(f"[Python] get_remaining() returned: ${result:.2f}")
            return float(result)
        except Exception as e:
            print(f"[Python] Error in get_remaining: {e}")
            return 0.0
    
    def get_item_count(self):
        """Get number of items"""
        if not self.cart_ptr:
            print("[Python] WARNING: Cart not created for get_item_count()")
            return 0
        
        try:
            result = self.lib.get_item_count(self.cart_ptr)
            print(f"[Python] get_item_count() returned: {result}")
            return int(result)
        except Exception as e:
            print(f"[Python] Error in get_item_count: {e}")
            return 0
    
    def set_category_budget(self, category_name, max_amount):
        """Set budget for a category"""
        if not self.cart_ptr:
            print("[Python] ERROR: Cart not created!")
            return False
        
        print(f"[Python] Setting category budget: {category_name} = ${max_amount}")
        
        try:
            result = self.lib.set_category_budget(
                self.cart_ptr,
                category_name.encode('utf-8'),
                ctypes.c_float(max_amount)
            )
            print(f"[Python] set_category_budget result: {result}")
            return bool(result)
        except Exception as e:
            print(f"[Python] Error in set_category_budget: {e}")
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
            print(f"[Python] get_category_spent({category_name}) = ${result:.2f}")
            return float(result)
        except Exception as e:
            print(f"[Python] Error in get_category_spent: {e}")
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
            print(f"[Python] get_category_remaining({category_name}) = ${result:.2f}")
            return float(result)
        except Exception as e:
            print(f"[Python] Error in get_category_remaining: {e}")
            return 0.0
    
    def print_state(self):
        """Print cart state for debugging"""
        if not self.cart_ptr:
            print("[Python] Cart not created")
            return "Cart not created"
        
        try:
            if hasattr(self.lib, 'print_cart_state'):
                print("[Python] ===== PRINTING CART STATE TO CONSOLE =====")
                self.lib.print_cart_state(self.cart_ptr)
                print("[Python] ===== END CART STATE =====")
                return "State printed to console"
        except Exception as e:
            print(f"[Python] Error in print_state: {e}")
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
            print(f"[Python] Error in get_display_working: {e}")
            # Fallback to simple display
            return self.get_simple_display()
    
    def debug_print(self):
        """Alias for print_state"""
        return self.print_state()
    
    def test(self):
        """Test the C library"""
        try:
            if hasattr(self.lib, 'test_cart'):
                print("[Python] ===== RUNNING C LIBRARY TEST =====")
                self.lib.test_cart()
                print("[Python] ===== TEST COMPLETE =====")
                return True
        except Exception as e:
            print(f"[Python] Error in test: {e}")
        return False
    
    def cleanup(self):
        """Free cart memory"""
        if self.cart_ptr:
            try:
                if hasattr(self.lib, 'free_cart'):
                    print("[Python] Freeing cart memory...")
                    self.lib.free_cart(self.cart_ptr)
                    print("[Python] Cart memory freed")
            except Exception as e:
                print(f"[Python] Error in cleanup: {e}")
            self.cart_ptr = None
    
    def get_removable_items(self, target_priority):
        """Get removable items - placeholder"""
        if not self.cart_ptr:
            return []
        
        try:
            # This function needs to be implemented in cart.c
            # For now, return empty list
            return []
        except:
            return []
