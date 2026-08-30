import { useEffect, useMemo, useState } from "react";

const PALETTE = {
  ".": "transparent",
  a: "#d6c8a2",
  b: "#2f2a4a",
  c: "#4a6fb5",
  d: "#79a7ff",
  e: "#f5d06f",
  f: "#ffffff",
  g: "#1b1b2f",
};

const BASE_FRAME = [
  "................",
  "......bbbb......",
  ".....bcccb......",
  "....bcddccb.....",
  "....bcddccb.....",
  "....bcaaacb.....",
  "....bafffab.....",
  "....baaaab......",
  "....bccccb......",
  "...bccggcccb....",
  "...bccggcccb....",
  "...bccggcccb....",
  "....bbggbb......",
  ".....bggb.......",
  ".....beeb.......",
  "................",
];

const FRAMES = {
  idle: [
    BASE_FRAME,
    [
      "................",
      "......bbbb......",
      ".....bcccb......",
      "....bcddccb.....",
      "....bcddccb.....",
      "....bcaaacb.....",
      "....baf.ffb.....",
      "....baaaab......",
      "....bccccb......",
      "...bccggcccb....",
      "...bccggcccb....",
      "...bccggcccb....",
      "....bbggbb......",
      ".....bggb.......",
      ".....beeb.......",
      "................",
    ],
  ],
  think: [
    BASE_FRAME,
    [
      "................",
      "......bbbb......",
      ".....bcccb...e..",
      "....bcddccb.ee..",
      "....bcddccb...e.",
      "....bcaaacb.....",
      "....bafffab.....",
      "....baaaab......",
      "....bccccb......",
      "...bccggcccb....",
      "...bccggcccb....",
      "...bccggcccb....",
      "....bbggbb......",
      ".....bggb.......",
      ".....beeb.......",
      "................",
    ],
  ],
  talk: [
    [
      "................",
      "......bbbb......",
      ".....bcccb......",
      "....bcddccb.....",
      "....bcddccb.....",
      "....bcaaacb.....",
      "....bafffab.....",
      "....baaabb......",
      "....bccccb......",
      "...bccggcccb....",
      "...bccggcccb....",
      "...bccggcccb....",
      "....bbggbb......",
      ".....bggb.......",
      ".....beeb.......",
      "................",
    ],
    [
      "................",
      "......bbbb......",
      ".....bcccb......",
      "....bcddccb.....",
      "....bcddccb.....",
      "....bcaaacb.....",
      "....bafffab.....",
      "....baaaab......",
      "....bccccb......",
      "...bccggcccb....",
      "...bccggcccb....",
      "...bccggcccb....",
      "....bbggbb......",
      ".....bggb.......",
      ".....beeb.......",
      "................",
    ],
  ],
  cast: [
    [
      "................",
      "......bbbb..e...",
      ".....bcccb.eee..",
      "....bcddccb..e..",
      "....bcddccb.....",
      "....bcaaacb.....",
      "....bafffab.....",
      "....baaaab......",
      "....bccccb......",
      "...bccggcccb....",
      "...bccggcccb....",
      "...bccggcccb....",
      "....bbggbb......",
      ".....bggb.......",
      ".....beeb.......",
      "................",
    ],
    [
      "................",
      "...e..bbbb..e...",
      "..eee.bcccb.eee.",
      "...e.bcddccb..e.",
      "....bcddccb.....",
      "....bcaaacb.....",
      "....bafffab.....",
      "....baaaab......",
      "....bccccb......",
      "...bccggcccb....",
      "...bccggcccb....",
      "...bccggcccb....",
      "....bbggbb......",
      ".....bggb.......",
      ".....beeb.......",
      "................",
    ],
  ],
};

const FPS = {
  idle: 3,
  think: 5,
  talk: 6,
  cast: 8,
};

export default function WizardSprite({ mood = "idle", scale = 4 }) {
  const [frameIndex, setFrameIndex] = useState(0);
  const frames = useMemo(() => FRAMES[mood] ?? FRAMES.idle, [mood]);

  useEffect(() => {
    setFrameIndex(0);
    const speed = 1000 / (FPS[mood] ?? FPS.idle);
    const id = setInterval(() => {
      setFrameIndex((v) => (v + 1) % frames.length);
    }, speed);
    return () => clearInterval(id);
  }, [frames, mood]);

  const frame = frames[frameIndex];
  const size = 16 * scale;
  const pixelSize = scale;

  return (
    <div
      className="rounded-lg border border-indigo-700 bg-slate-950 p-2"
      style={{ width: size + 16, height: size + 16 }}
      aria-label="Wizard tutor mascot"
    >
      <div
        className="grid"
        style={{
          width: size,
          height: size,
          gridTemplateColumns: `repeat(16, ${pixelSize}px)`,
          gridTemplateRows: `repeat(16, ${pixelSize}px)`,
          imageRendering: "pixelated",
        }}
      >
        {frame.flatMap((row, y) =>
          row.split("").map((cell, x) => (
            <span
              key={`${x}-${y}`}
              style={{
                width: pixelSize,
                height: pixelSize,
                backgroundColor: PALETTE[cell] ?? "transparent",
              }}
            />
          ))
        )}
      </div>
    </div>
  );
}
