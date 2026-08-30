import { useEffect, useMemo, useState } from "react";

// Palette sampled/matched from the reference artwork
const PALETTE = {
  ".": "transparent",
  k: "#13203a", // darkest navy (outlines, book cover)
  n: "#20385c", // dark navy (hat/robe shading)
  m: "#2c4a72", // mid navy-blue (robe/hat body)
  b: "#5e6fbe", // main robe/hat blue
  c: "#83a3c2", // soft blue highlight
  l: "#84baea", // bright hat highlight
  s: "#fad1b6", // skin
  w: "#fafafa", // beard / book pages
  g: "#b8c4d7", // pale blue-grey highlight
  d: "#938f95", // grey shadow accents
  y: "#f6d272", // gold (gem, trim)
  z: "#ffe98a", // bright gold glow (casting)
};

const BG = "#c4d4e3"; // background lifted from the artwork

const BASE = [
  "..............bbbbbg............",
  ".............dclbbmnd...........",
  ".............dlllbnmmc..........",
  ".............clllmmmmmg.........",
  "..............lllmmgmng.........",
  "............dlllbbnccd..........",
  "...........gdlllbbmm............",
  "...........bglllbbmnc...........",
  "..........gnllllbbmkc...........",
  ".........dbmlllllbbmmd..........",
  "........mbblllllllllmmm.........",
  "........bbbmnkknnkkkmmmn........",
  "........kkkmmndddmmdkkkb........",
  ".........cngskdssksddkg.........",
  ".........gm.sssgssssgkg.........",
  ".........dmwww.g..ww.ng.........",
  ".........mmwwwwwwwwwgnb.........",
  "........cbbwwwwwwwwwbmmg........",
  "........bbmdwwwwwww.mmmd........",
  ".......gbbdgddwwwwbdgmmmg.......",
  ".......cbmmdyyygyywyymmmc.......",
  ".......mlmmmmdsddgmkddmmm.......",
  "......gblmmmmmnddkkkknmmmg......",
  "......dbcmmmmmmnnkkkkmmmmc......",
  "......dbmdsmmmmnyknmnsmmmc......",
  "......dbmdskmmnykymnnsdmmc......",
  "......dmmkknmnynykydnkkmmc......",
  ".......mnkknnnnykykkkkkmm.......",
  ".......dmkknnnnnkkkkmmkmc.......",
  ".......cmmmbnmkdmknmmmmmg.......",
  "........mmmcm.cnmcdmmmmm........",
  "........gnbcmw.g..dbmmmg........",
  ".........mbcmww...dbmmb.........",
  ".........mbcmww...dbbmb.........",
  "........gnbcmww...dbmmn.........",
  ".cgg.ccgcnbmbwwg..cmmmmcgcgccgc.",
  "cbbbbbbbmnmmmggdccmmmmmmcbbbbbbc",
  "bbbbbbbbbmmmmmmmmmmmmmmbbbbbbbbb"
];

const BLINK = [
  "..............bbbbbg............",
  ".............dclbbmnd...........",
  ".............dlllbnmmc..........",
  ".............clllmmmmmg.........",
  "..............lllmmgmng.........",
  "............dlllbbnccd..........",
  "...........gdlllbbmm............",
  "...........bglllbbmnc...........",
  "..........gnllllbbmkc...........",
  ".........dbmlllllbbmmd..........",
  "........mbblllllllllmmm.........",
  "........bbbmnkknnkkkmmmn........",
  "........kkkmmndddmmdkkkb........",
  ".........cngssdssdsddkg.........",
  ".........gm.sssgssssgkg.........",
  ".........dmwww.g..ww.ng.........",
  ".........mmwwwwwwwwwgnb.........",
  "........cbbwwwwwwwwwbmmg........",
  "........bbmdwwwwwww.mmmd........",
  ".......gbbdgddwwwwbdgmmmg.......",
  ".......cbmmdyyygyywyymmmc.......",
  ".......mlmmmmdsddgmkddmmm.......",
  "......gblmmmmmnddkkkknmmmg......",
  "......dbcmmmmmmnnkkkkmmmmc......",
  "......dbmdsmmmmnyknmnsmmmc......",
  "......dbmdskmmnykymnnsdmmc......",
  "......dmmkknmnynykydnkkmmc......",
  ".......mnkknnnnykykkkkkmm.......",
  ".......dmkknnnnnkkkkmmkmc.......",
  ".......cmmmbnmkdmknmmmmmg.......",
  "........mmmcm.cnmcdmmmmm........",
  "........gnbcmw.g..dbmmmg........",
  ".........mbcmww...dbmmb.........",
  ".........mbcmww...dbbmb.........",
  "........gnbcmww...dbmmn.........",
  ".cgg.ccgcnbmbwwg..cmmmmcgcgccgc.",
  "cbbbbbbbmnmmmggdccmmmmmmcbbbbbbc",
  "bbbbbbbbbmmmmmmmmmmmmmmbbbbbbbbb"
];

const CAST = [
  "..............bbbbbgz...........",
  ".............dclbbmnd.z.........",
  ".............dlllbnmmc.z........",
  ".............clllmmmmmg.........",
  "..............lllmmgmng.........",
  "............dlllbbnccd..........",
  "...........gdlllbbmm............",
  "...........bglllbbmnc...........",
  "..........gnllllbbmkc...........",
  ".........dbmlllllbbmmd..........",
  "........mbblllllllllmmm.........",
  "........bbbmnkknnkkkmmmn........",
  "........kkkmdndddmmdkkkb........",
  ".........cngskdssdkddkg.........",
  ".........gm.sssgssssgkg.........",
  ".........dmwww.g..ww.ng.........",
  ".........mmwwwwwwwwwgnb.........",
  "........cbbwwwwwwwwwbmmg........",
  "........bbmdwwwwwww.mmmd........",
  ".......gbbdgddwwwwbdgmmmg.......",
  ".......cbmmdzzzgzzwzzmmmc.......",
  ".......mlmmmmdsddgmkddmmm.......",
  "......gblmmmmmnddkkkknmmmg......",
  "......dbcmmmmmmnnkkkkmmmmc......",
  "......dbmdsmmmmnzknmnsmmmc......",
  "......dbmdskmmnzkzmnnsdmmc......",
  "......dmmkknmnznzkzdnkkmmc......",
  ".......mnkknnnnzkzkkkkkmm.......",
  ".......dmkknnnnnkkkkmmkmc.......",
  ".......cmmmbnmkdmknmmmmmg.......",
  "........mmmcm.cnmcdmmmmm........",
  "........gnbcmw.g..dbmmmg........",
  ".........mbcmww...dbmmb.........",
  ".........mbcmww...dbbmb.........",
  "........gnbcmww...dbmmn.........",
  ".cgg.ccgcnbmbwwg..cmmmmcgcgccgc.",
  "cbbbbbbbmnmmmggdccmmmmmmcbbbbbbc",
  "bbbbbbbbbmmmmmmmmmmmmmmbbbbbbbbb"
];

const THINK = [
  "..............bbbbbg............",
  ".............dclbbmnd.y.........",
  ".............dlllbnmmc..........",
  ".............clllmmmmmg.........",
  "..............lllmmgmng.........",
  "............dlllbbnccd..........",
  "...........gdlllbbmm............",
  "...........bglllbbmnc...........",
  "..........gnllllbbmkc...........",
  ".........dbmlllllbbmmd..........",
  "........mbblllllllllmmm.........",
  "........bbbmnkknnkkkmmmn........",
  "........kkkmdndddmmdkkkb........",
  ".........cngskdssdkddkg.........",
  ".........gm.sssgssssgkg.........",
  ".........dmwww.g..ww.ng.........",
  ".........mmwwwwwwwwwgnb.........",
  "........cbbwwwwwwwwwbmmg........",
  "........bbmdwwwwwww.mmmd........",
  ".......gbbdgddwwwwbdgmmmg.......",
  ".......cbmmdyyygyywyymmmc.......",
  ".......mlmmmmdsddgmkddmmm.......",
  "......gblmmmmmnddkkkknmmmg......",
  "......dbcmmmmmmnnkkkkmmmmc......",
  "......dbmdsmmmmnyknmnsmmmc......",
  "......dbmdskmmnykymnnsdmmc......",
  "......dmmkknmnynykydnkkmmc......",
  ".......mnkknnnnykykkkkkmm.......",
  ".......dmkknnnnnkkkkmmkmc.......",
  ".......cmmmbnmkdmknmmmmmg.......",
  "........mmmcm.cnmcdmmmmm........",
  "........gnbcmw.g..dbmmmg........",
  ".........mbcmww...dbmmb.........",
  ".........mbcmww...dbbmb.........",
  "........gnbcmww...dbmmn.........",
  ".cgg.ccgcnbmbwwg..cmmmmcgcgccgc.",
  "cbbbbbbbmnmmmggdccmmmmmmcbbbbbbc",
  "bbbbbbbbbmmmmmmmmmmmmmmbbbbbbbbb"
];

const FRAMES = {
  idle: [BASE, BASE, BLINK, BASE],
  think: [BASE, THINK, BASE, THINK],
  talk: [BASE, BLINK, BASE, BASE],
  cast: [BASE, CAST, BASE, CAST],
};

const FPS = {
  idle: 2,
  think: 3,
  talk: 5,
  cast: 6,
};

export default function WizardSprite({ mood = "idle", scale = 6 }) {
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
  const width = frame[0].length;
  const height = frame.length;
  const pixelSize = scale;

  return (
    <div
      style={{
        display: "inline-flex",
        borderRadius: 12,
        padding: 16,
        background: BG,
      }}
      aria-label="Wizard tutor mascot"
    >
      <div
        style={{
          width: width * pixelSize,
          height: height * pixelSize,
          display: "grid",
          gridTemplateColumns: `repeat(${width}, ${pixelSize}px)`,
          gridTemplateRows: `repeat(${height}, ${pixelSize}px)`,
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
