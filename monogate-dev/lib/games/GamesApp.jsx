import { BrowserRouter, Routes, Route, useNavigate, Navigate } from "react-router-dom";
import Hub from "./monogate-games-hub";
import MagicBrick from "./magic-brick-math";
import EmlBuilder from "./eml-builder";
import Strata from "./strata";
import Shadow from "./shadow";
import Measure from "./measure";
import Closure from "./closure";
import Genesis from "./genesis";
import Proof from "./proof";
import TheGap from "./the-gap";
import ConveyorSim from "./conveyor-sim";
import DepthOfRoom from "./depth-of-room";
import MonogateSound from "./monogate-sound";
import Cosmos from "./cosmos";
import PhantomAttractor from "./phantom-attractor";
import IdentityTheorem from "./identity-theorem";
import NegativeExponent from "./negative-exponent";
import WeierstrasMachine from "./weierstrass-machine";
import BillionTrees from "./billion-trees";
import EMLSynth from "./eml-synth";
import FractalStudio from "./fractal-studio";
import EMLSynthesizer from "./eml-synthesizer";

function BackButton() {
  const nav = useNavigate();
  return (
    <button
      onClick={() => nav("/")}
      style={{
        position: "fixed", top: 16, left: 16, zIndex: 9999,
        background: "rgba(8,6,14,0.75)", border: "1px solid rgba(167,139,250,0.2)",
        backdropFilter: "blur(8px)", WebkitBackdropFilter: "blur(8px)",
        color: "#A78BFA", borderRadius: 8, padding: "7px 14px", cursor: "pointer",
        fontSize: 13, fontFamily: "system-ui, sans-serif",
        display: "flex", alignItems: "center", gap: 6,
        transition: "border-color 0.2s",
      }}
      onMouseEnter={e => e.currentTarget.style.borderColor = "rgba(167,139,250,0.5)"}
      onMouseLeave={e => e.currentTarget.style.borderColor = "rgba(167,139,250,0.2)"}
    >
      ← hub
    </button>
  );
}

function Game({ children }) {
  return (
    <>
      <BackButton />
      {children}
    </>
  );
}

export default function GamesApp() {
  return (
    <BrowserRouter basename="/lab">
      <Routes>
        <Route path="/" element={<Hub />} />
        <Route path="/magic-brick" element={<Game><MagicBrick /></Game>} />
        <Route path="/eml-builder" element={<Game><EmlBuilder /></Game>} />
        <Route path="/strata" element={<Game><Strata /></Game>} />
        <Route path="/shadow" element={<Game><Shadow /></Game>} />
        <Route path="/measure" element={<Game><Measure /></Game>} />
        <Route path="/closure" element={<Game><Closure /></Game>} />
        <Route path="/genesis" element={<Game><Genesis /></Game>} />
        <Route path="/proof" element={<Game><Proof /></Game>} />
        <Route path="/the-gap" element={<Game><TheGap /></Game>} />
        <Route path="/conveyor-sim" element={<Game><ConveyorSim /></Game>} />
        <Route path="/depth-of-room" element={<Game><DepthOfRoom /></Game>} />
        <Route path="/monogate-sound" element={<Game><MonogateSound /></Game>} />
        <Route path="/cosmos" element={<Game><Cosmos /></Game>} />
        <Route path="/phantom-attractor" element={<Game><PhantomAttractor /></Game>} />
        <Route path="/identity-theorem" element={<Game><IdentityTheorem /></Game>} />
        <Route path="/negative-exponent" element={<Game><NegativeExponent /></Game>} />
        <Route path="/weierstrass-machine" element={<Game><WeierstrasMachine /></Game>} />
        <Route path="/billion-trees" element={<Game><BillionTrees /></Game>} />
        <Route path="/eml-synth" element={<Game><EMLSynth /></Game>} />
        <Route path="/fractal-studio" element={<Game><FractalStudio /></Game>} />
        <Route path="/fractal-explorer" element={<Navigate to="/fractal-studio" replace />} />
        <Route path="/eml-synthesizer" element={<Game><EMLSynthesizer /></Game>} />
      </Routes>
    </BrowserRouter>
  );
}
