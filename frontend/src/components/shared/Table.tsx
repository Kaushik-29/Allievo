import React from "react";
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

interface Column<T> {
  header: string;
  accessor: keyof T | ((item: T) => React.ReactNode);
  className?: string;
}

interface TableProps<T> {
  data: T[];
  columns: Column<T>[];
  className?: string;
  onRowClick?: (item: T) => void;
}

export const Table = <T extends { id: string | number }>({
  data,
  columns,
  className,
  onRowClick,
}: TableProps<T>) => {
  return (
    <div className={cn("overflow-x-auto rounded-3xl border border-gray-100", className)}>
      <table className="w-full text-left border-collapse">
        <thead>
          <tr className="bg-gray-50/50">
            {columns.map((col, i) => (
              <th
                key={i}
                className={cn(
                  "px-6 py-4 text-[10px] font-bold uppercase tracking-widest text-gray-400 border-b border-gray-100",
                  col.className
                )}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {data.map((item) => (
            <tr
              key={item.id}
              onClick={() => onRowClick?.(item)}
              className={cn(
                "transition-colors group",
                onRowClick ? "cursor-pointer hover:bg-gray-50/80 active:bg-gray-100" : ""
              )}
            >
              {columns.map((col, j) => (
                <td
                  key={j}
                  className={cn(
                    "px-6 py-5 text-sm text-gray-700 font-medium whitespace-nowrap transition-transform duration-200 group-active:scale-[0.99]",
                    col.className
                  )}
                >
                  {typeof col.accessor === "function" ? col.accessor(item) : (item[col.accessor] as React.ReactNode)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
