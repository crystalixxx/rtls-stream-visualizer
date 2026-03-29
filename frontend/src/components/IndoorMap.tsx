import { useCallback, useRef, useState } from "react";
import type { Position } from "../types";
import { TagMarker } from "./TagMarker";

const PLAN_WIDTH = 800;
const PLAN_HEIGHT = 600;

interface Props {
  positions: Map<string, Position>;
  selectedTagId: string | null;
  onSelectTag: (tagId: string) => void;
  showTags?: boolean;
  invertY?: boolean;
}

export function IndoorMap({
  positions,
  selectedTagId,
  onSelectTag,
  showTags = true,
  invertY = false,
}: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const dragRef = useRef<{
    startX: number;
    startY: number;
    ox: number;
    oy: number;
  } | null>(null);

  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault();
    setScale((s) => Math.max(0.25, Math.min(4, s - e.deltaY * 0.001)));
  }, []);

  const handleMouseDown = useCallback(
    (e: React.MouseEvent) => {
      if (e.button !== 0) return;
      dragRef.current = {
        startX: e.clientX,
        startY: e.clientY,
        ox: offset.x,
        oy: offset.y,
      };
    },
    [offset],
  );

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.startX;
    const dy = e.clientY - dragRef.current.startY;
    setOffset({ x: dragRef.current.ox + dx, y: dragRef.current.oy + dy });
  }, []);

  const handleMouseUp = useCallback(() => {
    dragRef.current = null;
  }, []);

  const indoorPositions = Array.from(positions.values()).filter(
    (p) => p.x != null && p.y != null,
  );

  return (
    <div
      ref={containerRef}
      className="relative h-full w-full overflow-hidden bg-gray-50 cursor-grab active:cursor-grabbing"
      onWheel={handleWheel}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      data-testid="indoor-map"
    >
      <div
        style={{
          transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
          transformOrigin: "0 0",
          width: PLAN_WIDTH,
          height: PLAN_HEIGHT,
        }}
        className="relative"
      >
        <img
          src="/floorplan.svg"
          alt="Floor plan"
          width={PLAN_WIDTH}
          height={PLAN_HEIGHT}
          draggable={false}
          className="select-none"
        />
        {showTags &&
          indoorPositions.map((pos) => (
            <div
              key={pos.tag_id}
              className="absolute -translate-x-1/2 -translate-y-1/2"
              style={{
                left: pos.x!,
                top: invertY ? PLAN_HEIGHT - pos.y! : pos.y!,
              }}
            >
              <TagMarker
                position={pos}
                coordSystem="indoor"
                selected={selectedTagId === pos.tag_id}
                onClick={() => onSelectTag(pos.tag_id)}
              />
            </div>
          ))}
      </div>
    </div>
  );
}
