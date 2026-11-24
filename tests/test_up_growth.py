"""Unit tests verifying exact High Utility Pattern Mining (UP-Growth & IHUP) calculations."""

import pytest
from src.data_loader import UtilityDataLoader
from src.up_growth import HighUtilityFPGrowthMiner
from src.ui.styles import get_custom_css

BENCHMARK_TRANS = """TID,Items
T1,"a:1, c:1, d:1"
T2,"a:2, c:6, e:2, g:5"
T3,"a:1, b:2, c:1, d:6, e:1, f:5"
T4,"b:4, c:3, d:3, e:1"
T5,"b:2, c:2, e:1, g:2"
"""

BENCHMARK_PROFITS = """Item,Profit
a,5
b,2
c,1
d,2
e,3
f,1
g,1
"""


class TestHighUtilityExtendedFPGrowth:
    """Verify TU, TWU, UP-Tree construction, DGU & DGN pruning, and exact HUP discovery."""

    def test_tu_and_twu_calculations(self) -> None:
        profits = UtilityDataLoader.parse_profit_table(BENCHMARK_PROFITS)
        transactions, _ = UtilityDataLoader.parse_transactions(BENCHMARK_TRANS, profits)
        assert len(transactions) == 5

        tu_map = {t.tid: t.transaction_utility for t in transactions}
        assert tu_map["T1"] == 8.0
        assert tu_map["T2"] == 27.0
        assert tu_map["T3"] == 30.0
        assert tu_map["T4"] == 20.0
        assert tu_map["T5"] == 11.0

        miner = HighUtilityFPGrowthMiner(use_dgn_pruning=True)
        miner.mine(transactions, min_utility=30.0)

        assert miner.initial_twu["c"] == 96.0
        assert miner.initial_twu["e"] == 88.0
        assert miner.initial_twu["a"] == 65.0
        assert miner.initial_twu["b"] == 61.0
        assert miner.initial_twu["d"] == 58.0

    def test_ihup_and_upgrowth_find_exact_same_hups(self) -> None:
        """Both IHUP (no DGN) and UP-Growth (with DGN) must return the exact same final HUPs."""
        profits = UtilityDataLoader.parse_profit_table(BENCHMARK_PROFITS)
        transactions, _ = UtilityDataLoader.parse_transactions(BENCHMARK_TRANS, profits)

        miner_ihup = HighUtilityFPGrowthMiner(use_dgn_pruning=False)
        miner_up = HighUtilityFPGrowthMiner(use_dgn_pruning=True)

        hups_ihup = miner_ihup.mine(transactions, min_utility=30.0)
        hups_up = miner_up.mine(transactions, min_utility=30.0)

        set_ihup = {(frozenset(h.items), h.exact_utility) for h in hups_ihup}
        set_up = {(frozenset(h.items), h.exact_utility) for h in hups_up}

        assert len(set_ihup) > 0
        assert set_ihup == set_up
        assert miner_up.candidate_count <= miner_ihup.candidate_count

    def test_dgu_and_dgn_reduce_node_utilities_correctly(self) -> None:
        profits = UtilityDataLoader.parse_profit_table(BENCHMARK_PROFITS)
        transactions, _ = UtilityDataLoader.parse_transactions(BENCHMARK_TRANS, profits)

        miner_ihup = HighUtilityFPGrowthMiner(use_dgn_pruning=False)
        miner_up = HighUtilityFPGrowthMiner(use_dgn_pruning=True)

        # At min_utility=35.0, item 'f' (TWU=30 < 35) is pruned by DGU, reducing RTU(T3) by 5 (from 30 to 25).
        # Thus under IHUP, root.children['c'].node_utility == 96 - 5 == 91.0
        # Under UP-Growth (DGN), root.children['c'].node_utility == sum of u(c, T) == 1+6+1+3+2 == 13.0
        miner_ihup.mine(transactions, min_utility=35.0)
        miner_up.mine(transactions, min_utility=35.0)

        c_node_ihup = miner_ihup.global_tree.root.children["c"]
        c_node_up = miner_up.global_tree.root.children["c"]
        assert c_node_ihup.node_utility == 91.0
        assert c_node_up.node_utility == 13.0

    def test_high_profit_low_frequency_item_discovery(self) -> None:
        """Verify that a low-frequency but high-profit item (e.g. Laptop) is discovered as a HUP."""
        trans_csv = 'TID,Items\nT1,"Laptop:1"\nT2,"Mouse:1"\nT3,"Mouse:1"\nT4,"Mouse:1"'
        prof_csv = "Item,Profit\nLaptop,1000\nMouse,10"
        profits = UtilityDataLoader.parse_profit_table(prof_csv)
        transactions, _ = UtilityDataLoader.parse_transactions(trans_csv, profits)

        miner = HighUtilityFPGrowthMiner(use_dgn_pruning=True)
        hups = miner.mine(transactions, min_utility=500.0)
        assert len(hups) == 1
        assert hups[0].items == ("Laptop",)
        assert hups[0].exact_utility == 1000.0

    def test_custom_css_valid(self) -> None:
        css = get_custom_css()
        assert "<style>" in css
        assert "Vazirmatn" in css
