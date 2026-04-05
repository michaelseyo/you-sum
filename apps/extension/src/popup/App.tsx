import { API_BASE_URL, ENV } from "../config/env";

export function App() {
  return (
    <main className="popup">
      <h1>Yousum</h1>
      <p className="status">Environment: {ENV}</p>
      <p className="status">API: {API_BASE_URL}</p>
      <pre>Extension migration scaffold in progress.</pre>
    </main>
  );
}
