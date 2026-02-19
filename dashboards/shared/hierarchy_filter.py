"""
Harris Farm Hub — Shared Product Hierarchy Filter
Reusable cascading sidebar filter: Department → Category → Sub-Category → HFM Item → Product.
Used by all transaction dashboards (Store Ops, Product Intel, Revenue Bridge, Buying Hub).
"""

import streamlit as st

from product_hierarchy import (
    get_departments, get_major_groups, get_minor_groups,
    get_hfm_items, get_products_in_hfm_item,
    search_hierarchy,
)


def render_hierarchy_filter(key_prefix="hf"):
    """Render cascading product hierarchy filters in the sidebar.

    Args:
        key_prefix: Unique prefix for widget keys (prevents collisions
                    when multiple dashboards use this component).

    Returns:
        dict with keys: dept_code, major_code, minor_code, hfm_item_code,
        product_number, day_type (each str or None, day_type always "all").
    """
    st.sidebar.markdown("### Product Filters")

    # Department selector
    departments = get_departments()
    dept_options = ["All Departments"] + [
        f"{d['name']} ({d['code']})" for d in departments
    ]
    dept_selection = st.sidebar.selectbox(
        "Department", dept_options, key=f"{key_prefix}_dept"
    )

    selected_dept_code = None
    selected_major_code = None
    selected_minor_code = None
    selected_hfm_item_code = None
    selected_product_number = None

    if dept_selection != "All Departments":
        selected_dept_code = next(
            (d["code"] for d in departments
             if f"{d['name']} ({d['code']})" == dept_selection),
            None,
        )

    # Major group selector (cascading)
    if selected_dept_code:
        major_groups = get_major_groups(selected_dept_code)
        mg_options = ["All Categories"] + [
            f"{m['name']} ({m['code']})" for m in major_groups
        ]
        mg_selection = st.sidebar.selectbox(
            "Category", mg_options, key=f"{key_prefix}_major"
        )
        if mg_selection != "All Categories":
            selected_major_code = next(
                (m["code"] for m in major_groups
                 if f"{m['name']} ({m['code']})" == mg_selection),
                None,
            )

    # Minor group selector (cascading)
    if selected_dept_code and selected_major_code:
        minor_groups = get_minor_groups(selected_dept_code, selected_major_code)
        mn_options = ["All Sub-Categories"] + [
            f"{m['name']} ({m['code']})" for m in minor_groups
        ]
        mn_selection = st.sidebar.selectbox(
            "Sub-Category", mn_options, key=f"{key_prefix}_minor"
        )
        if mn_selection != "All Sub-Categories":
            selected_minor_code = next(
                (m["code"] for m in minor_groups
                 if f"{m['name']} ({m['code']})" == mn_selection),
                None,
            )

    # HFM Item selector (cascading from minor group)
    if selected_dept_code and selected_major_code and selected_minor_code:
        hfm_items = get_hfm_items(
            selected_dept_code, selected_major_code, selected_minor_code)
        if hfm_items:
            hfm_options = ["All HFM Items"] + [
                f"{h['name']} ({h['code']})" for h in hfm_items
            ]
            hfm_selection = st.sidebar.selectbox(
                "HFM Item", hfm_options, key=f"{key_prefix}_hfm"
            )
            if hfm_selection != "All HFM Items":
                selected_hfm_item_code = next(
                    (h["code"] for h in hfm_items
                     if f"{h['name']} ({h['code']})" == hfm_selection),
                    None,
                )

    # Product/SKU selector (cascading from HFM item)
    if (selected_dept_code and selected_major_code
            and selected_minor_code and selected_hfm_item_code):
        products = get_products_in_hfm_item(
            selected_dept_code, selected_major_code,
            selected_minor_code, selected_hfm_item_code)
        if products:
            prod_options = ["All Products"] + [
                f"{p['product_name']} ({p['product_number']})" for p in products
            ]
            prod_selection = st.sidebar.selectbox(
                "Product/SKU", prod_options, key=f"{key_prefix}_product"
            )
            if prod_selection != "All Products":
                selected_product_number = next(
                    (p["product_number"] for p in products
                     if f"{p['product_name']} ({p['product_number']})" == prod_selection),
                    None,
                )

    # Reset filters button
    if selected_dept_code:
        if st.sidebar.button("Clear Product Filters", key=f"{key_prefix}_reset"):
            for k in [f"{key_prefix}_dept", f"{key_prefix}_major",
                       f"{key_prefix}_minor", f"{key_prefix}_hfm",
                       f"{key_prefix}_product"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    st.sidebar.markdown("---")

    return {
        "dept_code": selected_dept_code,
        "major_code": selected_major_code,
        "minor_code": selected_minor_code,
        "hfm_item_code": selected_hfm_item_code,
        "product_number": selected_product_number,
        "day_type": "all",
    }


def render_searchable_hierarchy_filter(key_prefix="hf"):
    """Render searchable product filter in sidebar.

    Single text input searches across PLU, product name, and all
    hierarchy levels. On selection, the full hierarchy is locked in.
    Works alongside render_hierarchy_filter() — both filters apply
    together (intersection).

    Returns same dict as render_hierarchy_filter():
        {dept_code, major_code, minor_code, hfm_item_code,
         product_number, day_type}
    """
    st.sidebar.markdown("### Search by PLU / Product")
    st.sidebar.caption("Works with the dropdown filters above.")

    search_query = st.sidebar.text_input(
        "Search by PLU or product name",
        value="",
        key=f"{key_prefix}_search",
        placeholder="e.g. 12345, Banana, Citrus...",
    )

    result = {
        "dept_code": None, "major_code": None, "minor_code": None,
        "hfm_item_code": None, "product_number": None, "day_type": "all",
    }

    if len(search_query.strip()) >= 2:
        matches = search_hierarchy(search_query, limit=50)

        if matches:
            options = ["Select a product..."] + [
                u"{name}  |  {dept} > {major} > {minor}  |  PLU: {plu}".format(
                    name=m["product_name"],
                    dept=m["dept_name"],
                    major=m["major_name"],
                    minor=m["minor_name"],
                    plu=m["product_number"],
                )
                for m in matches
            ]

            selection = st.sidebar.selectbox(
                "{n} result{s}".format(
                    n=len(matches),
                    s="s" if len(matches) != 1 else "",
                ),
                options,
                key=f"{key_prefix}_search_results",
            )

            if selection != "Select a product...":
                idx = options.index(selection) - 1
                selected = matches[idx]

                result["dept_code"] = selected["dept_code"]
                result["major_code"] = selected["major_code"]
                result["minor_code"] = selected["minor_code"]
                result["hfm_item_code"] = selected["hfm_item_code"]
                result["product_number"] = selected["product_number"]

                st.sidebar.success(
                    "{name} (PLU: {plu})\n\n"
                    "{dept} > {major} > {minor} > {hfm}".format(
                        name=selected["product_name"],
                        plu=selected["product_number"],
                        dept=selected["dept_name"],
                        major=selected["major_name"],
                        minor=selected["minor_name"],
                        hfm=selected["hfm_item_name"],
                    )
                )
        else:
            st.sidebar.warning("No products found.")

    elif len(search_query.strip()) == 1:
        st.sidebar.caption("Type at least 2 characters to search.")

    if any(result[k] for k in ["dept_code", "major_code", "minor_code",
                                 "hfm_item_code", "product_number"]):
        if st.sidebar.button("Clear Product Filter",
                              key=f"{key_prefix}_clear"):
            for k in [f"{key_prefix}_search",
                       f"{key_prefix}_search_results"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()

    st.sidebar.markdown("---")
    return result


def hierarchy_filter_summary(hierarchy, dept_list=None):
    """Build a human-readable label for the active hierarchy filters.

    Args:
        hierarchy: dict returned by render_hierarchy_filter().
        dept_list: optional pre-loaded department list (avoids re-query).

    Returns:
        str label like "Fruit & Vegetables > Citrus > Oranges", or None if no filter.
    """
    parts = []

    if hierarchy.get("dept_code"):
        departments = dept_list or get_departments()
        dept_name = next(
            (d["name"] for d in departments if d["code"] == hierarchy["dept_code"]),
            hierarchy["dept_code"],
        )
        label = dept_name

        if hierarchy.get("major_code"):
            major_groups = get_major_groups(hierarchy["dept_code"])
            mg_name = next(
                (m["name"] for m in major_groups
                 if m["code"] == hierarchy["major_code"]),
                hierarchy["major_code"],
            )
            label += f" > {mg_name}"

            if hierarchy.get("minor_code"):
                minor_groups = get_minor_groups(
                    hierarchy["dept_code"], hierarchy["major_code"])
                mn_name = next(
                    (m["name"] for m in minor_groups
                     if m["code"] == hierarchy["minor_code"]),
                    hierarchy["minor_code"],
                )
                label += f" > {mn_name}"

                if hierarchy.get("hfm_item_code"):
                    hfm_items = get_hfm_items(
                        hierarchy["dept_code"], hierarchy["major_code"],
                        hierarchy["minor_code"])
                    hfm_name = next(
                        (h["name"] for h in hfm_items
                         if h["code"] == hierarchy["hfm_item_code"]),
                        hierarchy["hfm_item_code"],
                    )
                    label += f" > {hfm_name}"

                    if hierarchy.get("product_number"):
                        prods = get_products_in_hfm_item(
                            hierarchy["dept_code"], hierarchy["major_code"],
                            hierarchy["minor_code"], hierarchy["hfm_item_code"])
                        prod_name = next(
                            (p["product_name"] for p in prods
                             if p["product_number"] == hierarchy["product_number"]),
                            hierarchy["product_number"],
                        )
                        label += f" > {prod_name}"

        parts.append(label)

    return " | ".join(parts) if parts else None
