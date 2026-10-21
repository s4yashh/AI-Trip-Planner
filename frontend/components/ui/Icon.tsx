/** Small inline SVG icon set (stroke icons, 24px grid). No icon library dependency. */
const PATHS = {
  home: "M3 10.5 12 3l9 7.5V20a1 1 0 0 1-1 1h-5v-6H9v6H4a1 1 0 0 1-1-1z",
  map: "M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2zM9 4v14M15 6v14",
  users: "M16 20v-1.5A3.5 3.5 0 0 0 12.5 15h-5A3.5 3.5 0 0 0 4 18.5V20M10 11a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7zM20 20v-1.5a3.5 3.5 0 0 0-2.5-3.35M15.5 4.15a3.5 3.5 0 0 1 0 6.7",
  plane: "M10.5 13.5 3 11l1.5-1.5 7.5 1L16.5 6a2.1 2.1 0 0 1 3 3L15 13.5l1 7.5-1.5 1.5-2.5-7.5-3 3V20l-1.5 1.5L6 18l-3.5-1.5L4 15h2.5z",
  bed: "M3 7v13M3 16h18M21 20v-7a3 3 0 0 0-3-3h-8v6M7 13a2 2 0 1 0 0-4 2 2 0 0 0 0 4z",
  info: "M12 21a9 9 0 1 0 0-18 9 9 0 0 0 0 18zM12 11v5M12 8h.01",
  menu: "M4 7h16M4 12h16M4 17h16",
  close: "M6 6l12 12M18 6 6 18",
  arrow: "M5 12h14M13 6l6 6-6 6",
  pin: "M12 21s-7-5.1-7-11a7 7 0 0 1 14 0c0 5.9-7 11-7 11zM12 12.5a2.5 2.5 0 1 0 0-5 2.5 2.5 0 0 0 0 5z",
} as const;

export type IconName = keyof typeof PATHS;

export function Icon({name, className = "h-5 w-5"}: {name: IconName; className?: string}) {
  return <svg viewBox="0 0 24 24" className={className} fill="none" stroke="currentColor" strokeWidth="1.8"
    strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={PATHS[name]}/></svg>;
}
