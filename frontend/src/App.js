import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

import Home from './pages/HomePage/home';
import Situation from './pages/SituationPage/situation';
import Result from './pages/ResultPage/result';

function App() {
  return (
    <Router>
      <div
        style={{
          background: "linear-gradient(135deg, #2f134bff 0%, #2d0c4d 100%)",
          minHeight: "100vh"
        }}
      >

        { /* App Routes */ }
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/situation" element={<Situation />} />
          <Route path="/result" element={<Result />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
