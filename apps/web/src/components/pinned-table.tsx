"use client";

import { useLayoutEffect, useRef, type CSSProperties, type ReactNode } from "react";

type PinnedTableProps = {
  /** 左边钉住几列。合同列表一般钉「文件名」这一列。 */
  pinLeft?: number;
  /** 右边钉住几列。合同列表一般钉「操作」这一列。 */
  pinRight?: number;
  /** 表格比这个宽度更宽时，中间列才能滑。不传则随内容变宽。 */
  minWidth?: number;
  children: ReactNode;
};

const PIN_CLASSES = [
  "ui-table-pin",
  "ui-table-pin-left",
  "ui-table-pin-right",
  "ui-table-pin-edge-left",
  "ui-table-pin-edge-right",
];

function clearPin(cell: HTMLElement) {
  cell.classList.remove(...PIN_CLASSES);
  cell.style.left = "";
  cell.style.right = "";
  cell.style.backgroundColor = "";
}

/**
 * 给一行里的格子算 sticky 偏移。
 *
 * 可以想成窗户：左右窗框钉死，中间玻璃能左右推。
 * 钉两列时，第二列不能也 left:0，否则会叠在第一列上，
 * 所以要把前面几列的宽度加起来，写成 left: 180px 这种。
 */
function pinRow(row: HTMLTableRowElement, pinLeft: number, pinRight: number) {
  const cells = Array.from(row.children) as HTMLElement[];
  cells.forEach(clearPin);

  // 空状态只有一个 colspan 格子，钉住没有意义。
  if (cells.length <= 1) return;

  const widths = cells.map((cell) => cell.getBoundingClientRect().width);
  const leftCount = Math.max(0, Math.min(pinLeft, cells.length));
  const rightCount = Math.max(0, Math.min(pinRight, cells.length - leftCount));

  let left = 0;
  for (let i = 0; i < leftCount; i += 1) {
    const cell = cells[i];
    cell.classList.add("ui-table-pin", "ui-table-pin-left");
    if (i === leftCount - 1) cell.classList.add("ui-table-pin-edge-left");
    cell.style.left = `${left}px`;
    cell.style.backgroundColor = cell.tagName === "TH" ? "var(--color-surface-alt)" : "var(--color-paper)";
    left += widths[i];
  }

  let right = 0;
  for (let i = 0; i < rightCount; i += 1) {
    const index = cells.length - 1 - i;
    const cell = cells[index];
    cell.classList.add("ui-table-pin", "ui-table-pin-right");
    if (i === rightCount - 1) cell.classList.add("ui-table-pin-edge-right");
    cell.style.right = `${right}px`;
    cell.style.backgroundColor = cell.tagName === "TH" ? "var(--color-surface-alt)" : "var(--color-paper)";
    right += widths[index];
  }
}

function applyPins(table: HTMLTableElement, pinLeft: number, pinRight: number) {
  table.querySelectorAll("tr").forEach((row) => {
    pinRow(row, pinLeft, pinRight);
  });
}

/**
 * 可横滑的表格。左右几列钉在窗口边上，中间列跟着滑。
 *
 * 用法和原来的 table 几乎一样，只是换成这个组件：
 *
 * ```tsx
 * <PinnedTable pinLeft={1} pinRight={1}>
 *   <thead>...</thead>
 *   <tbody>...</tbody>
 * </PinnedTable>
 * ```
 *
 * 不引入新的表格库，钉住靠浏览器的 position: sticky。
 */
export function PinnedTable({ pinLeft = 1, pinRight = 1, minWidth, children }: PinnedTableProps) {
  const wrapRef = useRef<HTMLDivElement>(null);
  const tableRef = useRef<HTMLTableElement>(null);

  useLayoutEffect(() => {
    const table = tableRef.current;
    const wrap = wrapRef.current;
    if (!table) return;

    const paint = () => applyPins(table, pinLeft, pinRight);
    paint();

    const observer = new ResizeObserver(paint);
    observer.observe(table);
    if (wrap) observer.observe(wrap);
    return () => observer.disconnect();
  }, [pinLeft, pinRight, children]);

  const tableStyle: CSSProperties | undefined = minWidth
    ? { minWidth: `${minWidth}px` }
    : undefined;

  return (
    <div ref={wrapRef} className="ui-card ui-pinned-table">
      <table ref={tableRef} className="ui-table" style={tableStyle}>
        {children}
      </table>
    </div>
  );
}
