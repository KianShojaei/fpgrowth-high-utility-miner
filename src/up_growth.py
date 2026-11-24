"""Extended FP-Growth for High Utility Pattern Mining (UP-Growth & IHUP-Growth Algorithms)."""

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set, Tuple

from src.data_loader import QuantitativeTransaction


@dataclass
class HighUtilityPattern:
    """Represents a discovered High Utility Itemset (HUP)."""

    items: Tuple[str, ...]
    exact_utility: float
    twu: float
    support_count: int
    relative_support: float
    utility_share_pct: float
    containing_tids: List[str]

    @property
    def k(self) -> int:
        return len(self.items)


class UPTreeNode:
    """A node in the Extended FP-Tree (UP-Tree / IHUP-Tree).

    Stores:
    - item: Item name (None for root)
    - count: Support count of transactions passing through this node
    - node_utility (nu): Accumulated utility upper-bound at this node
    - parent: Pointer to parent UPTreeNode
    - children: Dict mapping child item -> UPTreeNode
    - node_link: Pointer to next UPTreeNode with the same item in Header Table
    """

    def __init__(
        self,
        item: Optional[str],
        count: int = 0,
        node_utility: float = 0.0,
        parent: Optional["UPTreeNode"] = None,
    ) -> None:
        self.item = item
        self.count = count
        self.node_utility = node_utility
        self.parent = parent
        self.children: Dict[str, "UPTreeNode"] = {}
        self.node_link: Optional["UPTreeNode"] = None


@dataclass
class HeaderTableEntry:
    """Entry in the UP-Tree Header Table sorted by TWU descending."""

    item: str
    twu: float
    support_count: int = 0
    head_node: Optional[UPTreeNode] = None


@dataclass
class PrefixPathInfo:
    """Represents a conditional prefix path extracted from the UP-Tree for a base item."""

    prefix_items: List[str]
    path_utility: float
    path_count: int


class UPTree:
    """Extended FP-Tree (Utility Pattern Tree) supporting both IHUP (Full TU) and UP-Growth (DGN Pruning)."""

    def __init__(self, f_list_order: List[str], twu_map: Dict[str, float], use_dgn: bool = True) -> None:
        self.root = UPTreeNode(item=None)
        self.f_list_order = f_list_order
        self.use_dgn = use_dgn
        self.header_table: Dict[str, HeaderTableEntry] = {
            item: HeaderTableEntry(item=item, twu=twu_map[item]) for item in f_list_order
        }

    def insert_reorganized_transaction(
        self,
        ordered_items: List[str],
        item_utilities: Dict[str, float],
        rtu: float,
    ) -> None:
        """Insert a TWU-ordered transaction into the UP-Tree.

        - If `use_dgn=False` (IHUP-Tree mode): each node in the path accumulates the full RTU.
        - If `use_dgn=True` (UP-Growth DGN mode): Discards Global Node utilities of descendant items
          in the path, so node utility at position `idx` only adds the prefix utility sum(u(i_0..i_idx)).
        """
        current = self.root
        running_prefix_utility = 0.0

        for item in ordered_items:
            running_prefix_utility += item_utilities.get(item, 0.0)
            added_utility = running_prefix_utility if self.use_dgn else rtu

            if item in current.children:
                child = current.children[item]
                child.count += 1
                child.node_utility += added_utility
            else:
                child = UPTreeNode(
                    item=item,
                    count=1,
                    node_utility=added_utility,
                    parent=current,
                )
                current.children[item] = child
                # Link into Header Table
                entry = self.header_table[item]
                if entry.head_node is None:
                    entry.head_node = child
                else:
                    curr_link = entry.head_node
                    while curr_link.node_link is not None:
                        curr_link = curr_link.node_link
                    curr_link.node_link = child

            self.header_table[item].support_count += 1
            current = child

    def insert_conditional_path(self, prefix_items: List[str], path_utility: float, path_count: int) -> None:
        """Insert a conditional prefix path into a conditional UP-Tree."""
        current = self.root
        for item in prefix_items:
            if item in current.children:
                child = current.children[item]
                child.count += path_count
                child.node_utility += path_utility
            else:
                child = UPTreeNode(
                    item=item,
                    count=path_count,
                    node_utility=path_utility,
                    parent=current,
                )
                current.children[item] = child
                entry = self.header_table[item]
                if entry.head_node is None:
                    entry.head_node = child
                else:
                    curr_link = entry.head_node
                    while curr_link.node_link is not None:
                        curr_link = curr_link.node_link
                    curr_link.node_link = child

            self.header_table[item].support_count += path_count
            current = child

    def get_tree_paths_summary(self) -> List[Dict[str, str]]:
        """Return a human-readable list of root-to-leaf branches for UI visualization."""
        branches: List[Dict[str, str]] = []

        def _dfs(node: UPTreeNode, path_acc: List[str]) -> None:
            if node.item is not None:
                path_acc.append(f"{node.item} (cnt={node.count}, nu={node.node_utility:.1f})")
            if not node.children:
                if path_acc:
                    branches.append(
                        {
                            "شاخه درخت (Root → Leaf Branch)": "{} ──► " + " ──► ".join(path_acc),
                            "عمق شاخه": str(len(path_acc)),
                        }
                    )
            else:
                for child in node.children.values():
                    _dfs(child, list(path_acc))

        _dfs(self.root, [])
        return branches


class HighUtilityFPGrowthMiner:
    """Mines High Utility Patterns by extending FP-Growth with TWU, DGU/DGN UP-Tree, and Conditional Trees."""

    def __init__(self, use_dgn_pruning: bool = True) -> None:
        """Initialize the miner.

        Args:
            use_dgn_pruning: If True, uses UP-Growth (DGU + DGN node utility tightening).
                             If False, uses IHUP-Growth (full RTU at every FP-Tree node).
        """
        self.use_dgn_pruning = use_dgn_pruning
        self.initial_twu: Dict[str, float] = {}
        self.f_list: List[str] = []
        self.global_tree: Optional[UPTree] = None
        self.reorganized_transactions: List[Dict[str, str]] = []
        self.conditional_bases_log: Dict[str, List[PrefixPathInfo]] = {}
        self.candidate_count: int = 0

    def mine(
        self,
        transactions: List[QuantitativeTransaction],
        min_utility: float,
    ) -> List[HighUtilityPattern]:
        """Run the complete two-phase Extended FP-Growth High Utility Pattern Mining algorithm."""
        if not transactions or min_utility <= 0:
            return []

        total_db_utility = sum(t.transaction_utility for t in transactions)

        # =====================================================================
        # Scan 1: Compute TU(Td) and TWU(i) for all items, build TWU-ordered F-List
        # =====================================================================
        twu_map: Dict[str, float] = {}
        for t in transactions:
            for item in t.item_quantities:
                twu_map[item] = twu_map.get(item, 0.0) + t.transaction_utility

        self.initial_twu = dict(twu_map)

        # DGU (Discarding Global Unpromising Items): keep only items with TWU(i) >= min_utility
        promising_items = [it for it, twu in twu_map.items() if twu >= min_utility]
        # Sort F-List in descending order of TWU (tie-break alphabetically)
        promising_items.sort(key=lambda it: (-twu_map[it], it))
        self.f_list = promising_items
        promising_set = set(promising_items)

        if not self.f_list:
            return []

        # =====================================================================
        # Scan 2: Reorganize transactions according to F-List and construct Global UP-Tree
        # =====================================================================
        self.global_tree = UPTree(
            f_list_order=self.f_list,
            twu_map=twu_map,
            use_dgn=self.use_dgn_pruning,
        )
        self.reorganized_transactions = []

        for t in transactions:
            ordered = [it for it in self.f_list if it in t.item_quantities]
            if not ordered:
                continue
            # Reorganized Transaction Utility (RTU): utility of remaining promising items
            rtu = sum(t.item_utilities[it] for it in ordered)
            self.global_tree.insert_reorganized_transaction(
                ordered_items=ordered,
                item_utilities=t.item_utilities,
                rtu=rtu,
            )
            self.reorganized_transactions.append(
                {
                    "TID": t.tid,
                    "تراکنش اصلی (Original)": ", ".join(f"{k}:{v}" for k, v in t.item_quantities.items()),
                    "TU(T)": f"{t.transaction_utility:.1f}",
                    "تراکنش بازآرایی‌شده (TWU-Ordered)": " → ".join(ordered),
                    "RTU(T)": f"{rtu:.1f}",
                }
            )

        # =====================================================================
        # Recursive Mining of Conditional UP-Trees (Bottom-Up along Header Table)
        # =====================================================================
        potential_huis: Dict[FrozenSet[str], float] = {}
        self.conditional_bases_log = {}
        self.candidate_count = 0

        self._mine_up_tree_recursive(
            tree=self.global_tree,
            alpha=(),
            min_utility=min_utility,
            potential_huis=potential_huis,
            is_top_level=True,
        )
        self.candidate_count = len(potential_huis)

        # =====================================================================
        # Phase 2: Exact Utility Verification of Candidate Patterns (PHUIs -> HUPs)
        # =====================================================================
        hups: List[HighUtilityPattern] = []
        num_trans = len(transactions)

        for itemset_key, estimated_bound in potential_huis.items():
            exact_util = 0.0
            exact_twu = 0.0
            sup_cnt = 0
            tids_list: List[str] = []

            for t in transactions:
                if itemset_key.issubset(t.item_quantities.keys()):
                    sup_cnt += 1
                    tids_list.append(t.tid)
                    exact_twu += t.transaction_utility
                    exact_util += sum(t.item_utilities[it] for it in itemset_key)

            if exact_util + 1e-9 >= min_utility:
                # Order items according to F-List for clean presentation
                ordered_tuple = tuple(sorted(itemset_key, key=lambda x: self.f_list.index(x)))
                share = (exact_util / total_db_utility * 100.0) if total_db_utility > 0 else 0.0
                hups.append(
                    HighUtilityPattern(
                        items=ordered_tuple,
                        exact_utility=exact_util,
                        twu=exact_twu,
                        support_count=sup_cnt,
                        relative_support=sup_cnt / num_trans,
                        utility_share_pct=share,
                        containing_tids=tids_list,
                    )
                )

        hups.sort(key=lambda h: (-h.exact_utility, h.k, h.items))
        return hups

    def _mine_up_tree_recursive(
        self,
        tree: UPTree,
        alpha: Tuple[str, ...],
        min_utility: float,
        potential_huis: Dict[FrozenSet[str], float],
        is_top_level: bool = False,
    ) -> None:
        """Recursively mine UP-Tree bottom-up by constructing conditional pattern bases & conditional trees."""
        # Traverse header table in reverse order of F-List (lowest TWU to highest TWU)
        for item in reversed(tree.f_list_order):
            entry = tree.header_table[item]
            if entry.head_node is None:
                continue

            # Compute sum of node utilities along the node-links for `item`
            path_utility_sum = 0.0
            curr = entry.head_node
            while curr is not None:
                path_utility_sum += curr.node_utility
                curr = curr.node_link

            # Pruning: if the accumulated node utility upper bound < min_utility, skip!
            if path_utility_sum + 1e-9 < min_utility:
                continue

            beta = alpha + (item,)
            potential_huis[frozenset(beta)] = path_utility_sum

            # Extract Conditional Pattern Base (Transformed Prefix Paths) for `beta`
            prefix_paths: List[PrefixPathInfo] = []
            local_twu: Dict[str, float] = {}

            curr = entry.head_node
            while curr is not None:
                path_u = curr.node_utility
                path_c = curr.count
                ancestors: List[str] = []
                parent = curr.parent
                while parent is not None and parent.item is not None:
                    ancestors.append(parent.item)
                    parent = parent.parent

                if ancestors:
                    ancestors.reverse()  # Top-down order from root
                    prefix_paths.append(
                        PrefixPathInfo(
                            prefix_items=ancestors,
                            path_utility=path_u,
                            path_count=path_c,
                        )
                    )
                    for anc_item in ancestors:
                        local_twu[anc_item] = local_twu.get(anc_item, 0.0) + path_u

                curr = curr.node_link

            if is_top_level:
                self.conditional_bases_log[item] = prefix_paths

            # Filter local promising items in conditional database
            cond_f_list = [
                it for it in tree.f_list_order if local_twu.get(it, 0.0) + 1e-9 >= min_utility
            ]
            if not cond_f_list:
                continue

            cond_set = set(cond_f_list)
            cond_tree = UPTree(f_list_order=cond_f_list, twu_map=local_twu, use_dgn=False)

            for pp in prefix_paths:
                filtered_prefix = [it for it in pp.prefix_items if it in cond_set]
                if filtered_prefix:
                    cond_tree.insert_conditional_path(
                        prefix_items=filtered_prefix,
                        path_utility=pp.path_utility,
                        path_count=pp.path_count,
                    )

            self._mine_up_tree_recursive(
                tree=cond_tree,
                alpha=beta,
                min_utility=min_utility,
                potential_huis=potential_huis,
                is_top_level=False,
            )
