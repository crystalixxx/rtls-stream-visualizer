export interface VisibleLayers {
  tags: boolean;
  anchors: boolean;
}

interface Props {
  layers: VisibleLayers;
  onChange: (layers: VisibleLayers) => void;
}

export function LayerToggles({ layers, onChange }: Props) {
  return (
    <div
      className="flex gap-4 border-b border-gray-200 px-3 py-2 text-xs"
      data-testid="layer-toggles"
    >
      <label className="flex items-center gap-1.5 cursor-pointer">
        <input
          type="checkbox"
          checked={layers.tags}
          onChange={(e) => onChange({ ...layers, tags: e.target.checked })}
          data-testid="toggle-tags"
        />
        <span className="text-gray-700">Tags</span>
      </label>
      <label className="flex items-center gap-1.5 cursor-pointer">
        <input
          type="checkbox"
          checked={layers.anchors}
          onChange={(e) => onChange({ ...layers, anchors: e.target.checked })}
          data-testid="toggle-anchors"
        />
        <span className="text-gray-700">Anchors</span>
      </label>
    </div>
  );
}
