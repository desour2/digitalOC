import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Home from './pages/HomePage/home';
import Situation from './pages/SituationPage/situation';

function App() {
  return (
    <Router>
      <div
        style={{
          background: "linear-gradient(135deg, #167050ff 0%, #176047ff 100%)",
          minHeight: "100vh"
        }}
      >

        { /* App Routes */ }
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/situation" element={<Situation />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
