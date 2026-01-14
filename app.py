import streamlit as st
import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import time
import ctypes

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import cart wrapper
try:
    from cart_wrapper import CartWrapper
    C_LIB_AVAILABLE = True
    print("[APP] C library available")
except ImportError as e:
    print(f"[APP] C library not available: {e}")
    C_LIB_AVAILABLE = False

# Page config
st.set_page_config(
    page_title="Smart Grocery Cart",
    page_icon="🛒",
    layout="wide"
)

# Categories
CATEGORIES = ["Dairy", "Vegetables", "Snacks", "Meat", "Beverages", "Other"]

# Initialize session state
if 'cart' not in st.session_state:
    st.session_state.cart = None
if 'budget' not in st.session_state:
    st.session_state.budget = 100.0
if 'items_demo' not in st.session_state:
    st.session_state.items_demo = []
if 'cart_created' not in st.session_state:
    st.session_state.cart_created = False
if 'category_budgets' not in st.session_state:
    st.session_state.category_budgets = {}
if 'last_update' not in st.session_state:
    st.session_state.last_update = time.time()
if 'debug_mode' not in st.session_state:
    st.session_state.debug_mode = False
if 'pending_add' not in st.session_state:
    st.session_state.pending_add = None
if 'show_removal_options' not in st.session_state:
    st.session_state.show_removal_options = False
if 'removable_items' not in st.session_state:
    st.session_state.removable_items = []

def create_budget_map(cart):
    """Create visual budget map with progress bars for each category"""
    
    # Category configuration
    categories = [
        {"name": "Dairy", "emoji": "🥛", "color": "#FFD700"},
        {"name": "Vegetables", "emoji": "🥦", "color": "#32CD32"},
        {"name": "Snacks", "emoji": "🍪", "color": "#FF6347"},
        {"name": "Meat", "emoji": "🍖", "color": "#DC143C"},
        {"name": "Beverages", "emoji": "🥤", "color": "#1E90FF"},
        {"name": "Other", "emoji": "📦", "color": "#9370DB"}
    ]
    
    st.subheader("📊 Category Budget Map")
    
    # Create two columns: visualization and data
    col1, col2 = st.columns([3, 2])
    
    with col1:
        # Create progress bars for each category
        for cat in categories:
            try:
                # Get category data from C backend
                spent = cart.get_category_spent(cat["name"])
                remaining = cart.get_category_remaining(cat["name"])
                total = spent + remaining
                
                if total > 0:  # Only show categories with budget set
                    percentage = (spent / total) * 100
                    
                    # Determine bar color based on usage
                    if percentage >= 90:
                        color = "#FF0000"  # Red
                        warning = " ⚠️ FULL!"
                    elif percentage >= 70:
                        color = "#FFA500"  # Orange
                        warning = " ⚠️"
                    else:
                        color = cat["color"]
                        warning = ""
                    
                    # Create progress bar
                    st.markdown(f"**{cat['emoji']} {cat['name']}**")
                    
                    # Custom progress bar using HTML (more control)
                    progress_html = f"""
                    <div style="margin: 5px 0;">
                        <div style="background-color: #f0f0f0; border-radius: 10px; height: 20px; width: 100%;">
                            <div style="background-color: {color}; border-radius: 10px; height: 100%; width: {percentage}%;"></div>
                        </div>
                        <div style="display: flex; justify-content: space-between; margin-top: 5px;">
                            <span>${spent:.2f} / ${total:.2f}</span>
                            <span><b>{percentage:.1f}%</b>{warning}</span>
                        </div>
                    </div>
                    """
                    st.markdown(progress_html, unsafe_allow_html=True)
                else:
                    st.markdown(f"**{cat['emoji']} {cat['name']}**")
                    st.info("No budget set for this category")
                    
            except Exception as e:
                # If C backend fails, show placeholder
                if st.session_state.debug_mode:
                    st.write(f"{cat['emoji']} {cat['name']}: Error - {str(e)}")
                else:
                    st.write(f"{cat['emoji']} {cat['name']}: Data unavailable")
    
    with col2:
        # Create summary table
        st.markdown("**💰 Category Summary**")
        
        summary_data = []
        total_spent_all = 0
        total_budget_all = 0
        
        for cat in categories:
            try:
                spent = cart.get_category_spent(cat["name"])
                remaining = cart.get_category_remaining(cat["name"])
                total = spent + remaining
                
                if total > 0:
                    percentage = (spent / total) * 100
                    summary_data.append({
                        "Category": f"{cat['emoji']} {cat['name']}",
                        "Spent": f"${spent:.2f}",
                        "Budget": f"${total:.2f}",
                        "Remaining": f"${remaining:.2f}",
                        "Usage": f"{percentage:.1f}%"
                    })
                    
                    total_spent_all += spent
                    total_budget_all += total
            except:
                pass
        
        if summary_data:
            # Display as table
            df = pd.DataFrame(summary_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Overall budget usage
            if total_budget_all > 0:
                overall_percentage = (total_spent_all / total_budget_all) * 100
                st.metric("Overall Budget Usage", f"{overall_percentage:.1f}%", 
                         f"${total_spent_all:.2f} / ${total_budget_all:.2f}")
        else:
            st.info("No category budgets set yet")

def create_pie_chart(cart):
    """Create pie chart visualization of category spending"""
    
    categories = ["Dairy", "Vegetables", "Snacks", "Meat", "Beverages", "Other"]
    colors = ['#FFD700', '#32CD32', '#FF6347', '#DC143C', '#1E90FF', '#9370DB']
    
    # Collect data
    labels = []
    sizes = []
    cat_colors = []
    
    for i, cat_name in enumerate(categories):
        try:
            spent = cart.get_category_spent(cat_name)
            if spent > 0:
                labels.append(cat_name)
                sizes.append(spent)
                cat_colors.append(colors[i])
        except:
            pass
    
    if sizes:  # Only create chart if we have data
        st.subheader("🥧 Spending Distribution")
        
        fig, ax = plt.subplots(figsize=(6, 6))
        wedges, texts, autotexts = ax.pie(sizes, labels=labels, colors=cat_colors, 
                                         autopct='%1.1f%%', startangle=90)
        
        # Add legend
        ax.legend(wedges, labels, title="Categories", loc="center left", 
                 bbox_to_anchor=(1, 0, 0.5, 1))
        
        # Equal aspect ratio ensures pie is drawn as a circle
        ax.axis('equal')  
        
        st.pyplot(fig)
    else:
        st.info("No spending data available for visualization")

def create_text_budget_bars(cart, compact=False):
    """Alternative: Simple text-based budget bars (no matplotlib needed)"""
    
    if not compact:
        st.subheader("📈 Budget Progress (Text Version)")
    
    categories = [
        ("🥛 Dairy", "Dairy"),
        ("🥦 Vegetables", "Vegetables"),
        ("🍪 Snacks", "Snacks"),
        ("🍖 Meat", "Meat"),
        ("🥤 Beverages", "Beverages"),
        ("📦 Other", "Other")
    ]
    
    has_data = False
    
    for display_name, cat_name in categories:
        try:
            spent = cart.get_category_spent(cat_name)
            remaining = cart.get_category_remaining(cat_name)
            total = spent + remaining
            
            if total > 0:
                has_data = True
                percentage = (spent / total) * 100
                
                # Create text progress bar (20 characters wide)
                bars = int(percentage / 5)  # Each █ = 5%
                progress_bar = "█" * bars + "░" * (20 - bars)
                
                # Color code with emoji indicators
                if percentage >= 90:
                    indicator = "🔴"
                elif percentage >= 70:
                    indicator = "🟡"
                else:
                    indicator = "🟢"
                
                if compact:
                    st.write(f"{indicator} **{display_name}**")
                    st.caption(f"${spent:.2f}/${total:.2f} ({percentage:.1f}%)")
                else:
                    st.write(f"{indicator} **{display_name}**")
                    st.code(f"{progress_bar} {percentage:.1f}% (${spent:.2f}/${total:.2f})")
            elif not compact:
                st.write(f"⚪ **{display_name}**")
                st.caption("No budget set")
                
        except Exception as e:
            if not compact:
                if st.session_state.debug_mode:
                    st.write(f"{display_name}: Error - {str(e)}")
                else:
                    st.write(f"{display_name}: Data unavailable")
    
    if not has_data and not compact:
        st.info("No category budgets set yet. Set budgets in the sidebar to see progress.")

# Function to add item with error handling - UPDATED with return code handling
def add_item_to_cart(item_name, item_price, item_priority, item_quantity, selected_category):
    if not st.session_state.cart_created:
        return False, "Cart not created"
    
    if C_LIB_AVAILABLE and st.session_state.cart:
        try:
            item_cost = item_price * item_quantity
            
            # Get current state BEFORE adding
            item_count_before = st.session_state.cart.get_item_count()
            total_before = st.session_state.cart.get_total()
            remaining_before = st.session_state.cart.get_remaining()
            
            # Check category budget if set
            if selected_category in st.session_state.category_budgets:
                cat_budget = st.session_state.category_budgets[selected_category]
                if cat_budget > 0:
                    cat_spent = st.session_state.cart.get_category_spent(selected_category)
                    if cat_spent + item_cost > cat_budget + 0.01:
                        st.write(f"[APP] Category budget check: {selected_category}: ${cat_spent:.2f} + ${item_cost:.2f} > ${cat_budget:.2f}")
            
            # Use C backend - note: now returns 0, 1, or 2
            result = st.session_state.cart.add_item(
                item_name, item_price, item_priority, item_quantity, selected_category
            )
            
            if result == 2:  # USER CONFIRMATION NEEDED
                st.session_state.pending_add = {
                    'name': item_name,
                    'price': item_price,
                    'priority': item_priority,
                    'quantity': item_quantity,
                    'category': selected_category
                }
                # Get removable items for display
                try:
                    removable_items = st.session_state.cart.get_removable_items(item_priority)
                    st.session_state.removable_items = removable_items
                except:
                    st.session_state.removable_items = []
                
                st.session_state.show_removal_options = True
                return False, f"❌ **{selected_category} budget exceeded!** Need user confirmation."
            
            elif result == 1:  # SUCCESS
                st.session_state.last_update = time.time()
                
                # Get updated info
                item_count_after = st.session_state.cart.get_item_count()
                total_after = st.session_state.cart.get_total()
                remaining_after = st.session_state.cart.get_remaining()
                
                # Check if items were removed
                if item_count_after < item_count_before:
                    items_removed = item_count_before - item_count_after
                    return True, f"✅ **{item_name}** added successfully!\n\n**Note:** {items_removed} lower priority item(s) were removed to make space.\n\n**Cart Status:** ${total_after:.2f} spent, {item_count_after} items, ${remaining_after:.2f} remaining"
                else:
                    return True, f"✅ **{item_name}** added successfully!\n\n**Cart Status:** ${total_after:.2f} spent, {item_count_after} items, ${remaining_after:.2f} remaining"
            
            else:  # FAILED (result == 0)
                # Get current state for error message
                item_count = st.session_state.cart.get_item_count()
                total = st.session_state.cart.get_total()
                remaining = st.session_state.cart.get_remaining()
                overall_budget = total + remaining
                
                error_msg = f"❌ Failed to add **{item_name}**.\n\n"
                error_msg += f"**Details:**\n"
                error_msg += f"- Item cost: ${item_cost:.2f}\n"
                error_msg += f"- Current total: ${total:.2f}\n"
                error_msg += f"- Budget: ${overall_budget:.2f}\n"
                error_msg += f"- Remaining: ${remaining:.2f}\n\n"
                
                # Check if it's a category budget issue
                if selected_category in st.session_state.category_budgets:
                    cat_budget = st.session_state.category_budgets[selected_category]
                    if cat_budget > 0:
                        cat_spent = st.session_state.cart.get_category_spent(selected_category)
                        error_msg += f"**Category Budget ({selected_category}):** ${cat_spent:.2f} / ${cat_budget:.2f}\n"
                
                error_msg += f"\n**Possible reasons:**\n"
                error_msg += f"1. Overall budget exceeded\n"
                error_msg += f"2. Category budget exceeded with no removable items\n"
                error_msg += f"3. Item priority too low (priority: {item_priority})"
                
                return False, error_msg
                
        except Exception as e:
            if st.session_state.debug_mode:
                import traceback
                return False, f"Error adding item:\n```\n{str(e)}\n{traceback.format_exc()}\n```"
            return False, f"Error adding item: {str(e)}"
    else:
        # Demo mode
        item_cost = item_price * item_quantity
        current_total = sum(item['price'] * item['quantity'] 
                          for item in st.session_state.items_demo)
        
        if current_total + item_cost <= st.session_state.budget:
            st.session_state.items_demo.append({
                'name': item_name,
                'price': item_price,
                'priority': item_priority,
                'quantity': item_quantity,
                'category': selected_category
            })
            st.session_state.last_update = time.time()
            new_total = current_total + item_cost
            return True, f"✅ **{item_name}** added successfully (demo mode)!\n\n**Total:** ${new_total:.2f}/{st.session_state.budget:.2f}"
        else:
            return False, f"❌ Budget exceeded! Could not add **{item_name}**.\n\n**Current:** ${current_total:.2f}, **Item:** ${item_cost:.2f}, **Budget:** ${st.session_state.budget:.2f}"

# Function to remove item
def remove_item_from_cart(item_name):
    if not st.session_state.cart_created:
        return False, "Cart not created"
    
    if C_LIB_AVAILABLE and st.session_state.cart:
        try:
            success = st.session_state.cart.remove_item(item_name)
            if success:
                st.session_state.last_update = time.time()
                
                # Get updated info
                item_count = st.session_state.cart.get_item_count()
                total = st.session_state.cart.get_total()
                
                return True, f"✅ **{item_name}** removed successfully!\n\n**Cart Status:** ${total:.2f} spent, {item_count} items"
            else:
                return False, f"❌ Item **{item_name}** not found in cart"
        except Exception as e:
            return False, f"Error removing item: {str(e)}"
    else:
        # Demo mode - remove by name
        for i, item in enumerate(st.session_state.items_demo):
            if item['name'] == item_name:
                st.session_state.items_demo.pop(i)
                st.session_state.last_update = time.time()
                current_total = sum(item['price'] * item['quantity'] 
                                  for item in st.session_state.items_demo)
                return True, f"✅ **{item_name}** removed successfully (demo mode)!\n\n**Total:** ${current_total:.2f}/{st.session_state.budget:.2f}"
        return False, f"❌ Item **{item_name}** not found in cart"

# Title
st.title("🛒 Smart Grocery Cart")
st.markdown("Priority-based shopping with budget constraints")

# Sidebar
with st.sidebar:
    st.header("💰 Cart Settings")
    
    # Debug toggle - FIXED KEY
    if st.checkbox("Debug Mode", value=st.session_state.debug_mode, key="debug_mode_checkbox"):
        st.session_state.debug_mode = True
        st.info("Debug mode enabled - check console for output")
    else:
        st.session_state.debug_mode = False
    
    budget = st.number_input(
        "Set your budget:",
        min_value=10.0,
        value=st.session_state.budget,
        step=10.0,
        key="budget_input_main"
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Create Cart", type="primary", key="create_cart_btn_main"):
            if C_LIB_AVAILABLE:
                try:
                    st.session_state.cart = CartWrapper()
                    if st.session_state.cart.create_cart(budget):
                        st.session_state.cart_created = True
                        st.session_state.budget = budget
                        st.session_state.category_budgets = {}
                        st.session_state.pending_add = None
                        st.session_state.show_removal_options = False
                        st.success(f"✅ Cart created with ${budget} budget!")
                        
                        # Initialize category budgets to 0
                        for category in CATEGORIES:
                            st.session_state.cart.set_category_budget(category, 0.0)
                        
                        if st.session_state.debug_mode:
                            st.write(f"Cart object created: {st.session_state.cart is not None}")
                            st.write(f"Cart pointer: {st.session_state.cart.cart_ptr if hasattr(st.session_state.cart, 'cart_ptr') else 'N/A'}")
                    else:
                        st.error("❌ Failed to create cart!")
                except Exception as e:
                    st.error(f"❌ Error creating cart: {str(e)}")
                    if st.session_state.debug_mode:
                        import traceback
                        st.error(traceback.format_exc())
            else:
                st.session_state.cart_created = True
                st.session_state.budget = budget
                st.session_state.items_demo = []
                st.session_state.category_budgets = {}
                st.session_state.pending_add = None
                st.session_state.show_removal_options = False
                st.success(f"✅ Demo cart created with ${budget} budget!")
    
    with col2:
        if st.button("Reset Cart", key="reset_cart_btn_main"):
            if C_LIB_AVAILABLE and st.session_state.cart:
                st.session_state.cart.cleanup()
            st.session_state.cart = None
            st.session_state.cart_created = False
            st.session_state.items_demo = []
            st.session_state.category_budgets = {}
            st.session_state.pending_add = None
            st.session_state.show_removal_options = False
            st.session_state.removable_items = []
            st.info("🔄 Cart reset!")
    
    # Category budgets section
    if st.session_state.cart_created and C_LIB_AVAILABLE and st.session_state.cart:
        st.divider()
        st.subheader("📋 Category Budgets")
        
        # Create expander for category budgets
        with st.expander("Set Category Budgets", expanded=True):
            for category in CATEGORIES:
                # Get current value from session state or use default
                default_value = st.session_state.category_budgets.get(category, 0.0)
                
                # Category budget input
                category_budget = st.number_input(
                    f"{category} Budget:",
                    min_value=0.0,
                    value=float(default_value),
                    step=5.0,
                    key=f"budget_{category}_input_main"
                )
                
                # Update button - FIXED KEY
                if st.button(f"Set {category}", key=f"set_{category}_btn"):
                    try:
                        if st.session_state.cart.set_category_budget(category, category_budget):
                            st.session_state.category_budgets[category] = category_budget
                            st.success(f"✅ Set ${category_budget:.2f} for {category}!")
                        else:
                            st.error(f"❌ Failed to set budget for {category}")
                    except Exception as e:
                        st.error(f"❌ Error setting category budget: {str(e)}")
    
    # Compact budget view in sidebar
    if st.session_state.cart and st.session_state.cart_created:
        st.divider()
        st.subheader("📊 Quick Budget View")
        
        try:
            if C_LIB_AVAILABLE:
                # Overall budget
                try:
                    total = st.session_state.cart.get_total()
                    remaining = st.session_state.cart.get_remaining()
                    overall_budget = total + remaining
                    
                    if overall_budget > 0:
                        percentage = (total / overall_budget) * 100
                        
                        # Color code based on usage
                        if percentage >= 90:
                            delta_color = "inverse"
                        elif percentage >= 70:
                            delta_color = "off"
                        else:
                            delta_color = "normal"
                        
                        st.metric("Overall", f"${total:.2f}/${overall_budget:.2f}", 
                                 f"{percentage:.1f}% used", delta_color=delta_color)
                        
                        # Category quick view
                        category_info = []
                        for category in CATEGORIES:
                            try:
                                spent = st.session_state.cart.get_category_spent(category)
                                remaining_cat = st.session_state.cart.get_category_remaining(category)
                                total_cat = spent + remaining_cat
                                
                                if total_cat > 0 and spent > 0:
                                    cat_percentage = (spent / total_cat) * 100
                                    if cat_percentage >= 90:
                                        emoji = "🔴"
                                    elif cat_percentage >= 70:
                                        emoji = "🟡"
                                    else:
                                        emoji = "🟢"
                                    
                                    # Short category names
                                    short_name = category[:3] if len(category) > 3 else category
                                    category_info.append(f"{emoji} {short_name}: ${spent:.2f}")
                            except:
                                continue
                        
                        if category_info:
                            st.caption("\n".join(category_info))
                    else:
                        st.info("Set a budget to see progress")
                except Exception as e:
                    if st.session_state.debug_mode:
                        st.error(f"Error getting budget data: {str(e)}")
                    else:
                        st.info("Budget data not available yet")
            else:
                # Demo mode
                total = sum(item['price'] * item['quantity'] 
                          for item in st.session_state.items_demo)
                remaining = st.session_state.budget - total
                
                if st.session_state.budget > 0:
                    percentage = (total / st.session_state.budget) * 100
                    st.metric("Overall", f"${total:.2f}/{st.session_state.budget:.2f}", 
                             f"{percentage:.1f}% used")
        except Exception as e:
            if st.session_state.debug_mode:
                st.error(f"Error in quick budget view: {str(e)}")
            else:
                st.info("Waiting for cart data...")

# Main content tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Add Items", "View Cart", "Budget", "Visualization", "Debug", "Help"])

with tab1:
    st.header("➕ Add Items to Cart")
    
    # Show removal options if needed
    if st.session_state.show_removal_options and st.session_state.pending_add:
        st.warning("🛑 Category budget exceeded! Choose items to remove:")
        
        with st.expander("📋 Item to add:", expanded=True):
            st.json(st.session_state.pending_add)
        
        st.subheader("🗑️ Available items to remove (lower priority):")
        
        if st.session_state.removable_items:
            # Display removable items as checkboxes
            selected_items = []
            for i, item in enumerate(st.session_state.removable_items):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    if st.checkbox(f"{item['name']} (${item['cost']:.2f})", key=f"remove_{i}"):
                        selected_items.append(item)
                with col2:
                    st.write(f"P: {item['priority']}")
                with col3:
                    st.write(f"Cat: {item['category']}")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Remove selected and add item", type="primary", key="confirm_remove_add"):
                    if selected_items:
                        # Remove selected items
                        for item in selected_items:
                            # We need to implement remove_selected_item in cart_wrapper.py
                            # For now, use remove_item_by_name
                            st.session_state.cart.remove_item(item['name'])
                        
                        # Now try to add the pending item again
                        pending = st.session_state.pending_add
                        success, message = add_item_to_cart(
                            pending['name'], pending['price'], pending['priority'],
                            pending['quantity'], pending['category']
                        )
                        
                        # Clear pending state
                        st.session_state.pending_add = None
                        st.session_state.show_removal_options = False
                        st.session_state.removable_items = []
                        
                        if success:
                            st.success(message)
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.warning("Please select at least one item to remove")
            
            with col2:
                if st.button("🔄 Try auto-add again", key="retry_auto_add"):
                    # Clear and retry
                    st.session_state.show_removal_options = False
                    st.rerun()
            
            with col3:
                if st.button("❌ Cancel addition", key="cancel_pending_add"):
                    st.session_state.pending_add = None
                    st.session_state.show_removal_options = False
                    st.session_state.removable_items = []
                    st.info("Addition cancelled")
                    st.rerun()
        else:
            st.info("No lower priority items available for removal")
            if st.button("❌ Cancel", key="cancel_no_items"):
                st.session_state.pending_add = None
                st.session_state.show_removal_options = False
                st.rerun()
    
    # Normal add item interface
    if not st.session_state.cart_created:
        st.warning("⚠️ Please create a cart first using the sidebar!")
        if st.button("Create Cart Now", key="create_from_tab1_btn"):
            st.rerun()  # Fixed: Refresh the page
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            item_name = st.text_input("Item Name", placeholder="e.g., Milk, Bread", key="add_item_name_tab1")
            item_price = st.number_input("Price ($)", min_value=0.01, value=2.99, step=0.1, key="add_item_price_tab1")
        
        with col2:
            item_priority = st.slider("Priority (1-10)", 1, 10, 5, 
                                    help="10 = Highest priority, 1 = Lowest priority", key="add_item_priority_tab1")
            item_quantity = st.number_input("Quantity", min_value=1, value=1, key="add_item_quantity_tab1")
        
        # Category selection
        selected_category = st.selectbox("Category", CATEGORIES, key="add_item_category_tab1")
        
        # Add button - FIXED KEY
        add_button_col1, add_button_col2 = st.columns([3, 1])
        with add_button_col1:
            if st.button("➕ Add to Cart", type="primary", key="add_item_button_tab1", use_container_width=True):
                if item_name and item_name.strip():
                    success, message = add_item_to_cart(item_name, item_price, item_priority, item_quantity, selected_category)
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("⚠️ Please enter an item name!")
        
        with add_button_col2:
            if st.button("🔄 Refresh", key="refresh_add_tab1"):
                st.rerun()
        
        # Show current category status if budget is set
        if selected_category in st.session_state.category_budgets:
            cat_budget = st.session_state.category_budgets[selected_category]
            if cat_budget > 0 and C_LIB_AVAILABLE and st.session_state.cart:
                try:
                    spent = st.session_state.cart.get_category_spent(selected_category)
                    percentage = (spent / cat_budget * 100) if cat_budget > 0 else 0
                    
                    if percentage >= 90:
                        color = "red"
                        emoji = "🔴"
                    elif percentage >= 70:
                        color = "orange"
                        emoji = "🟡"
                    else:
                        color = "green"
                        emoji = "🟢"
                    
                    st.info(f"{emoji} **{selected_category}:** ${spent:.2f}/${cat_budget:.2f} ({percentage:.1f}% used)")
                except:
                    pass
        
        # Show priority explanation
        st.divider()
        with st.expander("📋 Priority Guide"):
            st.markdown("""
            ### Priority Scale (1-10):
            
            | Priority | Description | Examples |
            |----------|-------------|----------|
            | **10** | Essential items | Medicine, baby formula, life necessities |
            | **9** | Basic necessities | Milk, bread, eggs, rice |
            | **8** | Important items | Meat, vegetables, fruits |
            | **7** | Regular items | Cheese, yogurt, snacks |
            | **6** | Common items | Drinks, cookies, canned food |
            | **5** | Regular purchases | Spices, condiments |
            | **4** | Nice to have | Ice cream, chocolate |
            | **3** | Luxury items | Premium brands, desserts |
            | **2** | Treats | Candy, chips |
            | **1** | Impulse buys | Gum, magazines |
            
            ### How Priority System Works:
            1. When you add an item, it checks if it fits within your budget
            2. If budget is **exceeded**, the system checks item priorities
            3. **Lower priority items** (1-5) may be removed to make space for **higher priority items** (6-10)
            4. Items with **same or higher priority** are never removed
            """)
        
        # Quick test buttons - FIXED KEYS
        if st.session_state.debug_mode:
            st.divider()
            st.subheader("🚀 Quick Test Items")
            
            test_col1, test_col2, test_col3 = st.columns(3)
            
            with test_col1:
                if st.button("Test: Milk", key="test_milk_tab1"):
                    success, message = add_item_to_cart("Milk", 3.50, 8, 1, "Dairy")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            with test_col2:
                if st.button("Test: Bread", key="test_bread_tab1"):
                    success, message = add_item_to_cart("Bread", 2.99, 5, 1, "Other")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
            
            with test_col3:
                if st.button("Test: Eggs", key="test_eggs_tab1"):
                    success, message = add_item_to_cart("Eggs", 4.00, 7, 1, "Dairy")
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

# Tab 2: View Cart
with tab2:
    st.header("📋 Shopping Cart")
    
    if not st.session_state.cart_created:
        st.info("🛒 Cart is empty. Add items using the 'Add Items' tab.")
    else:
        if C_LIB_AVAILABLE and st.session_state.cart:
            try:
                # FIRST show metrics at the TOP
                item_count = st.session_state.cart.get_item_count()
                total = st.session_state.cart.get_total()
                remaining = st.session_state.cart.get_remaining()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Items in Cart", item_count)
                with col2:
                    st.metric("Total Spent", f"${total:.2f}")
                with col3:
                    st.metric("Remaining", f"${remaining:.2f}")
                
                # Show status message
                if item_count > 0:
                    st.success(f"✅ Cart has **{item_count} items** totaling **${total:.2f}**")
                else:
                    st.warning("🛒 Cart is empty. Add items using the 'Add Items' tab.")
                
                # Get display from C - USING IMPROVED METHOD
                display_text = st.session_state.cart.get_display()
                st.code(display_text, language=None)
                # Show the cart ALWAYS
                
                
                # Debug info in expander
                if st.session_state.debug_mode:
                    with st.expander("🔧 Debug Info"):
                        st.write(f"**Display text length:** {len(display_text) if display_text else 0}")
                        st.write(f"**Display preview:** '{display_text[:100] if display_text else 'None'}...'")
                        st.write(f"**Item count from C:** {item_count}")
                        st.write(f"**Total from C:** ${total:.2f}")
                        st.write(f"**Remaining from C:** ${remaining:.2f}")
                        
                        if st.button("Print Cart State to Console", key="print_state_tab2"):
                            result = st.session_state.cart.print_state()
                            st.write("Check console for output")
                
                # Show category summary if available
                try:
                    cat_summary = st.session_state.cart.get_category_summary()
                    if cat_summary and "Error" not in cat_summary and "No categories" not in cat_summary:
                        st.subheader("📊 Category Summary")
                        st.text(cat_summary)
                except Exception as e:
                    if st.session_state.debug_mode:
                        st.write(f"Category summary error: {e}")
                
                # Remove item section
                st.divider()
                st.subheader("🗑️ Remove Item")
                
                remove_col1, remove_col2 = st.columns([3, 1])
                with remove_col1:
                    remove_name = st.text_input("Enter item name to remove:", 
                                              placeholder="e.g., Milk, Bread",
                                              key="remove_item_name_tab2")
                
                with remove_col2:
                    st.write("")  # Spacer
                    st.write("")  # Spacer
                    if st.button("Remove Item", type="secondary", key="remove_item_button_tab2"):
                        if remove_name and remove_name.strip():
                            success, message = remove_item_from_cart(remove_name)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        else:
                            st.warning("⚠️ Please enter an item name")
                
                # Quick refresh button - FIXED KEY
                if st.button("🔄 Refresh Cart View", key="refresh_cart_view_tab2"):
                    st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error accessing cart: {str(e)}")
                if st.session_state.debug_mode:
                    import traceback
                    st.error(traceback.format_exc())
                    
                # Fallback: Try to show basic info
                st.info("Showing basic cart information...")
                try:
                    item_count = st.session_state.cart.get_item_count()
                    total = st.session_state.cart.get_total()
                    remaining = st.session_state.cart.get_remaining()
                    st.write(f"**Items in cart:** {item_count}")
                    st.write(f"**Total spent:** ${total:.2f}")
                    st.write(f"**Remaining budget:** ${remaining:.2f}")
                except:
                    st.warning("Unable to retrieve cart information")
        else:
            # Demo mode display (same as before)
            st.write("**Mode:** Demo (C library not available)")
            
            if st.session_state.items_demo:
                # Sort by priority
                sorted_items = sorted(
                    st.session_state.items_demo, 
                    key=lambda x: x['priority'], 
                    reverse=True
                )
                
                # Display as table
                st.write(f"**Items in Cart ({len(sorted_items)})**")
                
                for i, item in enumerate(sorted_items):
                    col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 1, 1, 1, 1])
                    
                    with col1:
                        st.write(f"**{item['name']}**")
                    with col2:
                        st.write(f"{item['category']}")
                    with col3:
                        st.write(f"${item['price']:.2f} × {item['quantity']}")
                    with col4:
                        st.write(f"P: {item['priority']}")
                    with col5:
                        item_total = item['price'] * item['quantity']
                        st.write(f"${item_total:.2f}")
                    with col6:
                        # FIXED KEY - use item name in key
                        if st.button("❌", key=f"remove_{item['name']}_{i}"):
                            st.session_state.items_demo.pop(i)
                            st.rerun()
                
                # Calculate totals
                grand_total = sum(item['price'] * item['quantity'] 
                                for item in st.session_state.items_demo)
                remaining = st.session_state.budget - grand_total
                
                # Display metrics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total", f"${grand_total:.2f}")
                with col2:
                    st.metric("Budget", f"${st.session_state.budget:.2f}")
                with col3:
                    st.metric("Remaining", f"${remaining:.2f}")
                
                # Progress bar
                if st.session_state.budget > 0:
                    usage = (grand_total / st.session_state.budget) * 100
                    st.progress(min(usage / 100, 1.0))
                    st.write(f"**Budget Usage: {usage:.1f}%**")
                
                # Category breakdown
                st.subheader("Category Breakdown")
                category_totals = {}
                for item in st.session_state.items_demo:
                    cat = item['category']
                    total = item['price'] * item['quantity']
                    category_totals[cat] = category_totals.get(cat, 0) + total
                
                for cat, total in category_totals.items():
                    st.write(f"**{cat}**: ${total:.2f}")
                    
                # Remove item section for demo mode
                st.divider()
                st.subheader("🗑️ Remove Item (Demo)")
                demo_remove_col1, demo_remove_col2 = st.columns([3, 1])
                with demo_remove_col1:
                    demo_remove_name = st.text_input("Enter item name:", 
                                                   placeholder="e.g., Milk",
                                                   key="demo_remove_item_name_tab2")
                with demo_remove_col2:
                    st.write("")
                    st.write("")
                    if st.button("Remove", key="demo_remove_button_tab2"):
                        if demo_remove_name:
                            found = False
                            for i, item in enumerate(st.session_state.items_demo):
                                if item['name'].lower() == demo_remove_name.lower():
                                    st.session_state.items_demo.pop(i)
                                    st.success(f"✅ Removed {demo_remove_name}")
                                    st.rerun()
                                    found = True
                                    break
                            if not found:
                                st.error(f"❌ Item '{demo_remove_name}' not found")
            else:
                st.info("🛒 Cart is empty. Add items using the 'Add Items' tab.")

# Tabs 3-6 remain mostly the same, but here's tab3 as an example
with tab3:
    st.header("💰 Budget Analysis")
    
    if not st.session_state.cart_created:
        st.info("Create a cart to see budget analysis.")
    else:
        try:
            if C_LIB_AVAILABLE and st.session_state.cart:
                # Get data directly
                total = st.session_state.cart.get_total()
                remaining = st.session_state.cart.get_remaining()
                item_count = st.session_state.cart.get_item_count()
                budget = total + remaining
                
                # Display main budget metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Budget", f"${budget:.2f}")
                with col2:
                    st.metric("Amount Spent", f"${total:.2f}")
                with col3:
                    st.metric("Remaining", f"${remaining:.2f}")
                with col4:
                    usage = (total / budget * 100) if budget > 0 else 0
                    st.metric("Usage", f"{usage:.1f}%")
                
                # Progress bar for overall budget
                if budget > 0:
                    usage = (total / budget) * 100
                    st.progress(min(usage / 100, 1.0))
                    
                    if usage >= 90:
                        st.error("⚠️ Budget nearly exhausted! Consider removing lower priority items.")
                    elif usage >= 70:
                        st.warning("⚠️ Budget usage is high")
                    else:
                        st.success(f"✅ Budget usage: {usage:.1f}%")
                
                # Try to get summary from cart
                try:
                    summary_text = st.session_state.cart.get_summary()
                    if summary_text and "Error" not in summary_text:
                        st.subheader("Detailed Summary")
                        st.text(summary_text)
                except:
                    pass
                
                # Category budgets
                st.subheader("📊 Category Budgets")
                category_data = []
                
                for category in CATEGORIES:
                    try:
                        spent = st.session_state.cart.get_category_spent(category)
                        remaining_cat = st.session_state.cart.get_category_remaining(category)
                        total_cat = spent + remaining_cat
                        
                        if total_cat > 0:
                            usage = (spent / total_cat) * 100 if total_cat > 0 else 0
                            category_data.append({
                                "Category": category,
                                "Spent": spent,
                                "Budget": total_cat,
                                "Remaining": remaining_cat,
                                "Usage": usage
                            })
                    except Exception as e:
                        if st.session_state.debug_mode:
                            st.write(f"Error getting {category}: {str(e)}")
                        continue
                
                if category_data:
                    for data in category_data:
                        col1, col2, col3, col4 = st.columns([2, 2, 3, 1])
                        with col1:
                            st.write(f"**{data['Category']}**")
                        with col2:
                            st.write(f"${data['Spent']:.2f} / ${data['Budget']:.2f}")
                        with col3:
                            st.progress(min(data['Usage'] / 100, 1.0))
                        with col4:
                            st.write(f"({data['Usage']:.1f}%)")
                else:
                    st.info("No category budgets set yet. Set budgets in the sidebar.")
                    
            else:
                # Demo mode
                total = sum(item['price'] * item['quantity'] 
                          for item in st.session_state.items_demo)
                remaining = st.session_state.budget - total
                item_count = len(st.session_state.items_demo)
                budget = st.session_state.budget
            
            # Display main budget metrics (fallback)
            if not C_LIB_AVAILABLE or not st.session_state.cart:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Budget", f"${budget:.2f}")
                with col2:
                    st.metric("Amount Spent", f"${total:.2f}")
                with col3:
                    st.metric("Remaining", f"${remaining:.2f}")
                with col4:
                    usage = (total / budget * 100) if budget > 0 else 0
                    st.metric("Usage", f"{usage:.1f}%")
                
                # Progress bar for overall budget
                if budget > 0:
                    usage = (total / budget) * 100
                    st.progress(min(usage / 100, 1.0))
                    st.write(f"**Budget Usage: {usage:.1f}%**")
                    
        except Exception as e:
            st.error(f"Error getting budget data: {e}")
            if st.session_state.debug_mode:
                import traceback
                st.error(traceback.format_exc())
            
            # Show basic info even if there's an error
            st.write("**Basic Info:**")
            try:
                if C_LIB_AVAILABLE and st.session_state.cart:
                    total = st.session_state.cart.get_total()
                    remaining = st.session_state.cart.get_remaining()
                    st.write(f"Total: ${total:.2f}")
                    st.write(f"Remaining: ${remaining:.2f}")
            except:
                pass

# Tab 4: Visualization
with tab4:
    st.header("📊 Budget Visualization")
    
    if st.session_state.cart and st.session_state.cart_created:
        # Choose visualization type
        viz_type = st.radio("Visualization Type:", 
                          ["Progress Bars", "Pie Chart", "Text Bars"],
                          key="viz_type_selector_tab4")
        
        if viz_type == "Progress Bars":
            create_budget_map(st.session_state.cart)
        elif viz_type == "Pie Chart":
            create_pie_chart(st.session_state.cart)
        else:
            create_text_budget_bars(st.session_state.cart, compact=False)
    else:
        st.info("Create a cart to see budget visualization")

# Tab 5: Debug
with tab5:
    st.header("🔧 Debug Information")
    
    st.write("### Session State")
    st.json({
        "cart_created": st.session_state.cart_created,
        "budget": st.session_state.budget,
        "C_LIB_AVAILABLE": C_LIB_AVAILABLE,
        "cart_object_exists": st.session_state.cart is not None,
        "demo_items_count": len(st.session_state.items_demo),
        "category_budgets": st.session_state.category_budgets,
        "last_update": time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update)),
        "debug_mode": st.session_state.debug_mode,
        "pending_add": st.session_state.pending_add is not None,
        "show_removal_options": st.session_state.show_removal_options
    })
    
    if C_LIB_AVAILABLE:
        st.write("### C Library Status")
        if st.session_state.cart:
            try:
                st.write(f"Cart pointer: {st.session_state.cart.cart_ptr}")
                st.write(f"Cart type: {type(st.session_state.cart)}")
                
                # Test display function
                if st.button("Test get_display()", key="test_display_tab5"):
                    try:
                        display = st.session_state.cart.get_display()
                        st.text_area("Display Result", display, height=200, key="display_result_tab5")
                        st.write(f"✅ Display length: {len(display)}")
                        
                        # Also test the working version
                        st.write("### get_display_working() result:")
                        display_working = st.session_state.cart.get_display_working()
                        st.text_area("Working Display Result", display_working, height=200, key="display_working_result_tab5")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                
                # Test basic functions
                if st.button("Test Basic Cart Functions", key="test_basic_tab5"):
                    try:
                        total = st.session_state.cart.get_total()
                        remaining = st.session_state.cart.get_remaining()
                        count = st.session_state.cart.get_item_count()
                        
                        st.write(f"✅ Total: ${total:.2f}")
                        st.write(f"✅ Remaining: ${remaining:.2f}")
                        st.write(f"✅ Item count: {count}")
                        
                        # Also test category functions
                        for category in CATEGORIES:
                            spent = st.session_state.cart.get_category_spent(category)
                            if spent > 0:
                                st.write(f"✅ {category}: ${spent:.2f}")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
                        
            except Exception as e:
                st.error(f"Error inspecting cart: {str(e)}")
        else:
            st.warning("Cart not created")
    
    st.write("### Test Priority System")
    if st.session_state.cart and st.session_state.cart_created and C_LIB_AVAILABLE:
        st.info("Use this section to test the priority-based replacement system")
        
        test_col1, test_col2, test_col3 = st.columns(3)
        
        with test_col1:
            if st.button("Test: Low Priority Item", key="test_low_tab5"):
                try:
                    result = st.session_state.cart.add_item("Low Priority Test", 30.0, 1, 1, "Other")
                    if result == 1:
                        st.success("✅ Added low priority item")
                        st.rerun()
                    elif result == 2:
                        st.warning("⚠️ User confirmation needed")
                    else:
                        st.error("❌ Failed to add low priority item")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with test_col2:
            if st.button("Test: Medium Priority Item", key="test_medium_tab5"):
                try:
                    result = st.session_state.cart.add_item("Medium Priority Test", 25.0, 5, 1, "Other")
                    if result == 1:
                        st.success("✅ Added medium priority item")
                        st.rerun()
                    elif result == 2:
                        st.warning("⚠️ User confirmation needed")
                    else:
                        st.error("❌ Failed to add medium priority item")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with test_col3:
            if st.button("Test: High Priority Item", key="test_high_tab5"):
                try:
                    result = st.session_state.cart.add_item("High Priority Test", 20.0, 10, 1, "Other")
                    if result == 1:
                        st.success("✅ Added high priority item")
                        st.rerun()
                    elif result == 2:
                        st.warning("⚠️ User confirmation needed")
                    else:
                        st.error("❌ Failed to add high priority item")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        if st.button("Print Cart State to Console", key="print_state_tab5"):
            try:
                result = st.session_state.cart.print_state()
                st.success("✅ Check console for output")
            except:
                st.error("❌ Debug function not available")
    
    if C_LIB_AVAILABLE and st.session_state.cart:
        st.write("### Run C Library Test")
        if st.button("Run C Library Test Function", key="run_test_tab5"):
            try:
                if st.session_state.cart.test():
                    st.success("✅ C library test completed - check console")
                else:
                    st.warning("⚠️ Test function not available in library")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    if st.button("🔄 Force Refresh", key="debug_refresh_tab5"):
        st.rerun()

# Tab 6: Help
with tab6:
    st.header("❓ Help & Instructions")
    
    st.markdown("""
    ## 🛒 How to Use Smart Grocery Cart
    
    ### 1. Create a Cart
    - Set your budget in the sidebar (minimum $10)
    - Click **"Create Cart"** to initialize
    - You'll see a success message when cart is created
    
    ### 2. Add Items
    - Go to **"Add Items"** tab
    - Enter item details:
        - **Name**: Item name (e.g., Milk, Bread)
        - **Price**: Cost per unit (e.g., 2.99)
        - **Priority**: Importance (1-10) - **READ BELOW**
        - **Quantity**: Number of units
        - **Category**: Item category
    
    ### 3. Priority System (IMPORTANT!)
    - **10**: Essential items (medicine, baby formula)
    - **9**: Basic necessities (milk, bread, eggs)
    - **8**: Important items (meat, vegetables)
    - **7**: Regular items (cheese, yogurt)
    - **6**: Common items (snacks, drinks)
    - **5**: Regular purchases
    - **4**: Nice to have
    - **3**: Luxury items
    - **2**: Treats
    - **1**: Impulse buys
    
    ### 4. Automatic Priority-Based Replacement
    When category budget is exceeded by adding a high-priority item:
    1. System first tries to remove lower priority items from **same category**
    2. If still over budget, shows you **lower priority items from all categories**
    3. You **select which items to remove**
    4. System removes selected items and adds new item
    
    ### 5. Category Budgets
    - Set individual budgets for each category in the sidebar
    - Click **"Set"** next to each category to allocate budget
    - Monitor spending per category in real-time
    - Category budgets prevent overspending in specific areas
    
    ### 6. View Your Cart
    - Go to **"View Cart"** tab to see all items
    - Shows item details, totals, and remaining budget
    - Remove items by entering their name
    
    ### 7. Budget Analysis
    - **"Budget"** tab shows detailed spending analysis
    - Visual progress bars for each category
    - Overall budget usage percentage
    
    ### 8. Visualizations
    - **"Visualization"** tab shows different views:
        - **Progress Bars**: Color-coded budget usage
        - **Pie Chart**: Spending distribution
        - **Text Bars**: Simple progress indicators
    
    ### 9. Debug Mode
    - Enable **Debug Mode** in sidebar for troubleshooting
    - Check **Debug** tab for detailed information
    - Shows console output and C library status
    
    ### 10. Common Issues & Solutions
    
    **Problem:** Cart shows as empty after adding items
    **Solution:** The display function has been fixed. Try refreshing or check console for errors.
    
    **Problem:** Items not being removed for priority
    **Solution:** Make sure new item has HIGHER priority (e.g., add priority 10 to replace priority 5)
    
    **Problem:** Can't add item even with budget available
    **Solution:** Check category budgets - they might be limiting specific categories
    
    **Problem:** C library not loading
    **Solution:** Make sure `cart.dll` (Windows) or `libcart.so` (Linux/Mac) is in the same directory
    
    ### Need More Help?
    - Check the console output for detailed error messages
    - Enable Debug Mode to see what's happening internally
    - Try the test buttons in the Debug tab
    """)

# Footer
st.markdown("---")
st.caption(f"🛒 Smart Grocery Cart System | Last update: {time.strftime('%H:%M:%S', time.localtime(st.session_state.last_update))}")

# Cleanup on app close
if C_LIB_AVAILABLE and st.session_state.cart:
    import atexit
    atexit.register(lambda: st.session_state.cart.cleanup() if st.session_state.cart else None)
