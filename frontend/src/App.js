// import logo from '../public/r-icon.png';
import './App.css';

function App() {
  return (
    <div className="App">

      <nav className="navbar">
        <div className="logo">REMEZ</div>
        <button className="login-btn">Login</button>
      </nav>

      <header className="App-header">
        {/* <img src={logo} className="App-logo" alt="logo" /> */}
        <h1 className="welcome-text">Welcome to REMEZ</h1>
        <p className="App-description">
          Advanced Medication Interaction Analysis
        </p>
      </header>
    </div>
  );
}

export default App;
