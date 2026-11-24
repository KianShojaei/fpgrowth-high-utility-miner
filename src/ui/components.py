"""Streamlit UI rendering components for Extended FP-Growth High Utility Pattern Mining."""

import html
from typing import Dict, List
import pandas as pd
import streamlit as st

from src.data_loader import QuantitativeTransaction
from src.up_growth import HighUtilityFPGrowthMiner, HighUtilityPattern


def render_header(dataset_title: str, algo_label: str, min_util: float) -> None:
    """Render hero header banner with Material Symbols icons."""
    header_html = (
        '<div class="app-hero-header">'
        '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 14px;">'
        '<div>'
        '<h1 style="display: flex; align-items: center; gap: 10px;">'
        '<span class="ms-icon" style="font-size: 2.1rem;">park</span>'
        '<span>استخراج الگوهای با مطلوبیت بالا با توسعه الگوریتم FP-Growth</span>'
        '</h1>'
        '<p>مبتنی بر ساختار درختی UP-Tree، خاصیت بستار رو به پایین TWU و استراتژی‌های هرس DGU و DGN</p>'
        '</div>'
        '<div style="display: flex; gap: 8px; flex-wrap: wrap; align-items: center;">'
        f'<span class="hero-pill"><span class="ms-icon">dataset</span> {html.escape(dataset_title)}</span>'
        f'<span class="hero-pill"><span class="ms-icon">bolt</span> روش: {html.escape(algo_label)}</span>'
        f'<span class="hero-pill" style="direction:ltr;">min_util = {min_util:,.1f}</span>'
        '</div></div></div>'
    )
    st.markdown(header_html, unsafe_allow_html=True)


def render_summary_kpis(
    transactions: List[QuantitativeTransaction],
    hups: List[HighUtilityPattern],
    candidate_count: int,
    promising_items_count: int,
) -> None:
    """Render top 4 KPI cards with clean RTL alignment."""
    total_db_utility = sum(t.transaction_utility for t in transactions)
    top_util = max((h.exact_utility for h in hups), default=0.0)

    kpi_html = (
        '<div class="kpi-grid">'
        '<div class="kpi-card">'
        '<div class="kpi-header-row"><span class="kpi-title">مجموع سود کل دیتابیس</span><span class="ms-icon" style="color:#0d9488;">payments</span></div>'
        f'<div class="kpi-value">{total_db_utility:,.1f}</div>'
        f'<div class="kpi-sub">در {len(transactions)} تراکنش کمی</div>'
        '</div>'
        '<div class="kpi-card">'
        '<div class="kpi-header-row"><span class="kpi-title">الگوهای با مطلوبیت بالا (HUPs)</span><span class="ms-icon" style="color:#0d9488;">workspace_premium</span></div>'
        f'<div class="kpi-value">{len(hups)}</div>'
        f'<div class="kpi-sub">بیشترین سود الگو: {top_util:,.1f}</div>'
        '</div>'
        '<div class="kpi-card">'
        '<div class="kpi-header-row"><span class="kpi-title">کاندیداهای درخت (PHUIs)</span><span class="ms-icon" style="color:#0d9488;">filter_alt</span></div>'
        f'<div class="kpi-value">{candidate_count}</div>'
        f'<div class="kpi-sub">استخراج‌شده از درخت‌های شرطی</div>'
        '</div>'
        '<div class="kpi-card">'
        '<div class="kpi-header-row"><span class="kpi-title">آیتم‌های امیدبخش (F-List)</span><span class="ms-icon" style="color:#0d9488;">format_list_numbered</span></div>'
        f'<div class="kpi-value">{promising_items_count}</div>'
        '<div class="kpi-sub">پس از هرس اولیه DGU (TWU ≥ min_util)</div>'
        '</div>'
        '</div>'
    )
    st.markdown(kpi_html, unsafe_allow_html=True)


def render_hups_section(hups: List[HighUtilityPattern], min_util: float) -> None:
    """Render discovered High Utility Patterns cards and downloadable CSV table."""
    if not hups:
        st.warning(f"هیچ الگویی با مطلوبیت بزرگ‌تر یا مساوی {min_util:,.1f} یافت نشد. لطفاً آستانه min_util را در نوار کناری کاهش دهید.")
        return

    st.markdown(
        f'<h3 style="display:flex; align-items:center; gap:8px;"><span class="ms-icon" style="color:#0d9488;">auto_awesome</span> الگوهای با مطلوبیت بالای کشف‌شده ({len(hups)} الگو)</h3>',
        unsafe_allow_html=True,
    )

    for idx, h in enumerate(hups[:12], start=1):
        badges_html = "".join(f'<span class="item-badge">{html.escape(it)}</span>' for it in h.items)
        tids_str = ", ".join(h.containing_tids)

        card_html = (
            f'<div class="hup-card">'
            f'<div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px; margin-bottom:10px;">'
            f'<div style="display:flex; align-items:center; gap:8px; flex-wrap:wrap;">'
            f'<span style="font-weight:900; color:#0d9488;">الگوی #{idx} ({h.k}-itemset):</span>'
            f'{badges_html}'
            f'</div>'
            f'<span class="share-badge">سهم از سود کل: {h.utility_share_pct:.1f}%</span>'
            f'</div>'
            f'<div style="display:flex; flex-wrap:wrap; gap:6px;">'
            f'<span class="metric-pill" style="border-color:rgba(13,148,136,0.5);"><b>Exact Utility u(X):</b> {h.exact_utility:,.1f}</span>'
            f'<span class="metric-pill"><b>TWU(X):</b> {h.twu:,.1f}</span>'
            f'<span class="metric-pill"><b>Support:</b> {h.support_count} ({h.relative_support*100:.1f}%)</span>'
            f'<span class="metric-pill"><b>TIDs:</b> {{{html.escape(tids_str)}}}</span>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

    st.markdown(
        '<h4 style="display:flex; align-items:center; gap:6px; margin-top:1.5rem;"><span class="ms-icon" style="color:#0d9488;">table_chart</span> جدول کامل الگوهای High Utility</h4>',
        unsafe_allow_html=True,
    )
    rows = []
    for idx, h in enumerate(hups, start=1):
        rows.append(
            {
                "#": idx,
                "الگو (Itemset X)": "{" + ", ".join(h.items) + "}",
                "طول الگو (k)": f"{h.k}-itemset",
                "سود دقیق u(X)": round(h.exact_utility, 2),
                "کران بالای TWU(X)": round(h.twu, 2),
                "تعداد تکرار sup(X)": h.support_count,
                "حمایت نسبی s(X)": f"{h.relative_support*100:.1f}%",
                "سهم از کل سود (%)": f"{h.utility_share_pct:.2f}%",
                "تراکنش‌های شامل الگو": "{" + ", ".join(h.containing_tids) + "}",
            }
        )

    df_hups = pd.DataFrame(rows)
    st.dataframe(df_hups, width="stretch", hide_index=True)

    csv_bytes = df_hups.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="خروجی CSV از جدول الگوهای High Utility",
        data=csv_bytes,
        file_name="high_utility_patterns.csv",
        mime="text/csv",
    )


def render_uptree_and_header_section(
    miner: HighUtilityFPGrowthMiner,
    min_util: float,
) -> None:
    """Render Header Table (TWU F-List), Reorganized Transactions, UP-Tree Branches, and Conditional Pattern Bases."""
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            '<h4 style="display:flex; align-items:center; gap:6px;"><span class="ms-icon" style="color:#0d9488;">sort</span> ۱. جدول هدر و محاسبه TWU آیتم‌ها (Header Table & DGU)</h4>',
            unsafe_allow_html=True,
        )
        header_rows = []
        for item, twu_val in sorted(miner.initial_twu.items(), key=lambda x: (-x[1], x[0])):
            is_promising = twu_val >= min_util
            sup_in_tree = (
                miner.global_tree.header_table[item].support_count
                if (miner.global_tree and item in miner.global_tree.header_table)
                else 0
            )
            header_rows.append(
                {
                    "آیتم (Item)": item,
                    "مقدار TWU(i)": round(twu_val, 2),
                    "شمارنده در درخت": sup_in_tree,
                    "وضعیت هرس DGU": "امیدبخش (در F-List)" if is_promising else "هرس‌شده (TWU < min_util)",
                }
            )
        st.dataframe(pd.DataFrame(header_rows), width="stretch", hide_index=True)

    with col2:
        st.markdown(
            '<h4 style="display:flex; align-items:center; gap:6px;"><span class="ms-icon" style="color:#0284c7;">swap_horiz</span> ۲. تراکنش‌های بازآرایی‌شده بر اساس F-List (Scan 2)</h4>',
            unsafe_allow_html=True,
        )
        if miner.reorganized_transactions:
            st.dataframe(pd.DataFrame(miner.reorganized_transactions), width="stretch", hide_index=True)
        else:
            st.info("هیچ تراکنش بازآرایی‌شده‌ای وجود ندارد.")

    st.markdown("---")
    st.markdown(
        '<h4 style="display:flex; align-items:center; gap:6px;"><span class="ms-icon" style="color:#0d9488;">account_tree</span> ۳. شاخه‌های درخت توسعه‌یافته UP-Tree (همراه با شمارنده و Node Utility هر گره)</h4>',
        unsafe_allow_html=True,
    )
    if miner.global_tree:
        branches = miner.global_tree.get_tree_paths_summary()
        if branches:
            st.dataframe(pd.DataFrame(branches), width="stretch", hide_index=True)

    st.markdown("---")
    st.markdown(
        '<h4 style="display:flex; align-items:center; gap:6px;"><span class="ms-icon" style="color:#0284c7;">call_split</span> ۴. پایگاه الگوهای شرطی استخراج‌شده از درخت (Conditional Pattern Bases)</h4>',
        unsafe_allow_html=True,
    )
    cond_rows = []
    for base_item, paths in miner.conditional_bases_log.items():
        if not paths:
            cond_rows.append(
                {
                    "آیتم پایه (Base Item)": base_item,
                    "مسیرهای پیشوندی شرطی (Transformed Prefix Paths)": "∅ (مستقیم زیر ریشه)",
                    "مجموع مطلوبیت مسیرهای شرطی": 0.0,
                }
            )
        else:
            formatted_paths = [
                f"[{' → '.join(p.prefix_items)} : cnt={p.path_count}, pu={p.path_utility:.1f}]"
                for p in paths
            ]
            cond_rows.append(
                {
                    "آیتم پایه (Base Item)": base_item,
                    "مسیرهای پیشوندی شرطی (Transformed Prefix Paths)": "  |  ".join(formatted_paths),
                    "مجموع مطلوبیت مسیرهای شرطی": round(sum(p.path_utility for p in paths), 2),
                }
            )
    if cond_rows:
        st.dataframe(pd.DataFrame(cond_rows), width="stretch", hide_index=True)


def render_dataset_and_profits_section(
    transactions: List[QuantitativeTransaction],
    profits: Dict[str, float],
) -> None:
    """Render quantitative transactions table and external profit table."""
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(
            '<h4 style="display:flex; align-items:center; gap:6px;"><span class="ms-icon" style="color:#0d9488;">receipt_long</span> جدول تراکنش‌های کمی و مطلوبیت هر تراکنش TU(T)</h4>',
            unsafe_allow_html=True,
        )
        t_rows = []
        for t in transactions:
            qty_str = ", ".join(f"{it} (×{q})" for it, q in t.item_quantities.items())
            util_str = " + ".join(f"{it}:{u:.1f}" for it, u in t.item_utilities.items())
            t_rows.append(
                {
                    "شناسه (TID)": t.tid,
                    "اقلام و تعداد خرید q(i, T)": qty_str,
                    "مطلوبیت تفکیکی اقلام u(i, T)": util_str,
                    "مطلوبیت کل تراکنش TU(T)": round(t.transaction_utility, 2),
                }
            )
        st.dataframe(pd.DataFrame(t_rows), width="stretch", hide_index=True)

    with col2:
        st.markdown(
            '<h4 style="display:flex; align-items:center; gap:6px;"><span class="ms-icon" style="color:#0284c7;">sell</span> جدول سود واحد کالاها (External Utility)</h4>',
            unsafe_allow_html=True,
        )
        p_rows = [
            {"آیتم (Item)": it, "سود واحد p(i)": round(val, 2)}
            for it, val in sorted(profits.items(), key=lambda x: (-x[1], x[0]))
        ]
        st.dataframe(pd.DataFrame(p_rows), width="stretch", hide_index=True)


def render_formulas_reference() -> None:
    """Render clean, pure-English LTR mathematical formulas for HUPM & UP-Growth."""
    st.markdown('<div class="math-ltr-box"><h4>1. Item Utility & Pattern Utility in Quantitative Database</h4></div>', unsafe_allow_html=True)
    st.latex(r"u(i, T_d) = q(i, T_d) \times p(i)")
    st.latex(r"u(X, T_d) = \sum_{i \in X} u(i, T_d), \qquad u(X) = \sum_{X \subseteq T_d \in \mathcal{D}} u(X, T_d)")

    st.markdown('<div class="math-ltr-box"><h4>2. Transaction Utility (TU) & Transaction-Weighted Utilization (TWU)</h4></div>', unsafe_allow_html=True)
    st.latex(r"TU(T_d) = \sum_{i \in T_d} u(i, T_d), \qquad TWU(X) = \sum_{X \subseteq T_d \in \mathcal{D}} TU(T_d)")
    st.latex(r"u(X) \le TWU(X), \qquad X \subseteq Y \implies TWU(Y) \le TWU(X) \quad (\text{TWU Anti-Monotonicity})")

    st.markdown('<div class="math-ltr-box"><h4>3. Extended FP-Growth Node Utility: IHUP vs. UP-Growth (DGU & DGN)</h4></div>', unsafe_allow_html=True)
    st.latex(r"RTU(T_d) = \sum_{i \in T_d \land TWU(i) \ge \text{min\_util}} u(i, T_d) \quad (\text{DGU Strategy})")
    st.latex(r"nu_{\text{IHUP}}(i_r) \mathrel{+}= RTU(T_d), \qquad nu_{\text{UP-Growth}}(i_r) \mathrel{+}= \sum_{j=1}^{r} u(i_j, T_d) \quad (\text{DGN Strategy})")
