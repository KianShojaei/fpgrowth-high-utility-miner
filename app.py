"""Extended FP-Growth High Utility Pattern Mining Web Application (Streamlit)."""

from pathlib import Path
import sys
import streamlit as st
from streamlit import runtime

if not runtime.exists():
    from streamlit.web import cli as stcli
    sys.argv = ["streamlit", "run", sys.argv[0]] + sys.argv[1:]
    sys.exit(stcli.main())

import config
from src.data_loader import UtilityDataLoader
from src.up_growth import HighUtilityFPGrowthMiner
from src.ui import (
    get_custom_css,
    render_dataset_and_profits_section,
    render_formulas_reference,
    render_header,
    render_hups_section,
    render_summary_kpis,
    render_uptree_and_header_section,
)

st.set_page_config(
    page_title="استخراج الگوهای با مطلوبیت بالا با توسعه FP-Growth",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(get_custom_css(), unsafe_allow_html=True)


def main() -> None:
    with st.sidebar:
        st.markdown(
            '<h3 style="display:flex; align-items:center; gap:8px;"><span class="ms-icon">tune</span> تنظیمات دیتاست و الگوریتم</h3>',
            unsafe_allow_html=True,
        )

        input_source = st.radio(
            "منبع دیتاست ورودی:",
            [
                "دیتاست‌های نمونه آماده",
                "آپلود فایل دیتاست (CSV)",
                "ورود یا ویرایش دستی تراکنش‌ها و سود",
            ],
        )

        raw_trans_csv = ""
        raw_profit_csv = ""
        dataset_title = ""
        default_min_u = 30

        if input_source == "دیتاست‌های نمونه آماده":
            preset_keys = list(config.PRESET_DATASETS.keys())
            selected_preset = st.selectbox(
                "انتخاب دیتاست:",
                options=preset_keys,
                format_func=lambda k: config.PRESET_DATASETS[k]["name"],
            )
            preset_info = config.PRESET_DATASETS[selected_preset]
            dataset_title = preset_info["name"].split("(")[0].strip()
            default_min_u = int(preset_info["default_min_util"])
            st.caption(preset_info["desc"])
            raw_trans_csv = Path(preset_info["trans_path"]).read_text(encoding="utf-8")
            raw_profit_csv = Path(preset_info["profit_path"]).read_text(encoding="utf-8")

        elif input_source == "آپلود فایل دیتاست (CSV)":
            up_trans = st.file_uploader("۱. فایل CSV تراکنش‌های کمی (فرمت Item:Qty):", type=["csv", "txt"])
            up_prof = st.file_uploader("۲. فایل CSV سود واحد کالاها (Item, Profit):", type=["csv", "txt"])
            if up_trans is not None:
                raw_trans_csv = up_trans.getvalue().decode("utf-8", errors="ignore")
                dataset_title = f"فایل آپلودشده ({up_trans.name})"
                if up_prof is not None:
                    raw_profit_csv = up_prof.getvalue().decode("utf-8", errors="ignore")
                else:
                    raw_profit_csv = ""
            else:
                st.info("لطفاً فایل تراکنش‌ها را آپلود کنید.")
                raw_trans_csv = Path(config.PRESET_DATASETS["benchmark"]["trans_path"]).read_text(encoding="utf-8")
                raw_profit_csv = Path(config.PRESET_DATASETS["benchmark"]["profit_path"]).read_text(encoding="utf-8")
                dataset_title = "دیتاست استاندارد مرجع"

        else:
            def_t = Path(config.PRESET_DATASETS["benchmark"]["trans_path"]).read_text(encoding="utf-8")
            def_p = Path(config.PRESET_DATASETS["benchmark"]["profit_path"]).read_text(encoding="utf-8")
            raw_trans_csv = st.text_area("تراکنش‌ها (فرمت Item:Quantity):", value=def_t, height=145)
            raw_profit_csv = st.text_area("جدول سود واحد (Item,Profit):", value=def_p, height=130)
            dataset_title = "دیتاست دستی کاربر"

        profits = UtilityDataLoader.parse_profit_table(raw_profit_csv)
        transactions, profits = UtilityDataLoader.parse_transactions(raw_trans_csv, profits)
        total_db_util = sum(t.transaction_utility for t in transactions) if transactions else 100.0

        st.markdown("---")
        st.markdown(
            '<div style="font-weight:700; display:flex; align-items:center; gap:6px; margin-bottom:6px;"><span class="ms-icon">sliders</span> آستانه حداقل مطلوبیت (min_util):</div>',
            unsafe_allow_html=True,
        )

        max_slider = max(int(total_db_util), 10)
        safe_default = min(default_min_u, max_slider)
        min_utility = float(
            st.slider(
                "حداقل سود / مطلوبیت (Minimum Utility):",
                min_value=1,
                max_value=max_slider,
                value=safe_default,
                step=max(1, max_slider // 50),
            )
        )

        st.markdown("---")
        st.markdown(
            '<div style="font-weight:700; display:flex; align-items:center; gap:6px; margin-bottom:6px;"><span class="ms-icon">memory</span> استراتژی توسعه درخت FP-Growth:</div>',
            unsafe_allow_html=True,
        )
        use_dgn = st.checkbox(
            "فعال‌سازی هرس پیشرفته UP-Growth (DGN + DGU)",
            value=True,
            help="در حالت فعال (UP-Growth)، سود آیتم‌های دنباله در گره‌های بالای درخت حذف می‌شود تا کران بالا کوچک‌تر شود. در حالت غیرفعال، الگوریتم به روش IHUP (ذخیره کل RTU در هر گره) عمل می‌کند.",
        )

    algo_label = "UP-Growth (DGU + DGN)" if use_dgn else "IHUP-Growth (TWU FP-Tree)"
    render_header(dataset_title=dataset_title, algo_label=algo_label, min_util=min_utility)

    if not transactions:
        st.error("دیتاست ورودی خالی است یا فرمت معتبری ندارد.")
        return

    miner = HighUtilityFPGrowthMiner(use_dgn_pruning=use_dgn)
    hups = miner.mine(transactions=transactions, min_utility=min_utility)

    render_summary_kpis(
        transactions=transactions,
        hups=hups,
        candidate_count=miner.candidate_count,
        promising_items_count=len(miner.f_list),
    )

    tab_hups, tab_tree, tab_data, tab_math = st.tabs([
        f"الگوهای با مطلوبیت بالا - HUPs ({len(hups)})",
        f"ساختار درخت UP-Tree و جدول هدر ({len(miner.f_list)} آیتم امیدبخش)",
        f"دیتابیس تراکنش‌های کمی و جدول سود ({len(transactions)} تراکنش)",
        "مرجع فرمول‌های ریاضی",
    ])

    with tab_hups:
        render_hups_section(hups=hups, min_util=min_utility)

    with tab_tree:
        render_uptree_and_header_section(miner=miner, min_util=min_utility)

    with tab_data:
        render_dataset_and_profits_section(transactions=transactions, profits=profits)

    with tab_math:
        render_formulas_reference()


if __name__ == "__main__":
    main()
