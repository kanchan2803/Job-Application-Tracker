import { useState, useEffect } from 'react';
import axios from 'axios';
import toast, { Toaster } from 'react-hot-toast';
import { Settings, Save, Briefcase, ExternalLink, RefreshCw } from 'lucide-react';

export default function App() {
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [jobs, setJobs] = useState([]); // Removed TypeScript <any[]>
  const [showSettings, setShowSettings] = useState(false);
  
  const [config, setConfig] = useState({
    backendUrl: localStorage.getItem('backendUrl') || 'http://localhost:8000',
    sheetUrl: localStorage.getItem('sheetUrl') || ''
  });

  useEffect(() => {
    if (config.sheetUrl) fetchJobs();
  }, [config]);

  const saveConfig = (newConfig) => {
    localStorage.setItem('backendUrl', newConfig.backendUrl);
    localStorage.setItem('sheetUrl', newConfig.sheetUrl);
    setConfig(newConfig);
    setShowSettings(false);
    toast.success('Settings saved!');
  };

  const fetchJobs = async () => {
    try {
      const res = await axios.get(`${config.backendUrl}/api/jobs`, {
        params: { sheet_url: config.sheetUrl }
      });
      setJobs(res.data.data);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveJob = async () => {
    if (!input.trim()) return toast.error('Paste a link or text first');
    if (!config.sheetUrl) return toast.error('Configure Google Sheet URL in settings');

    setLoading(true);
    try {
      await axios.post(`${config.backendUrl}/api/jobs`, {
        input_text: input,
        sheet_url: config.sheetUrl
      });
      toast.success('Job saved successfully!');
      setInput('');
      fetchJobs();
    } catch (error) {
      toast.error('Failed to save job');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-8 font-sans">
      <Toaster position="top-center" />
      
      {/* Header */}
      <div className="max-w-xl mx-auto flex justify-between items-center mb-8">
        <h1 className="text-xl font-bold flex items-center gap-2">
          <Briefcase className="w-6 h-6 text-blue-600" />
          Job Tracker
        </h1>
        <button onClick={() => setShowSettings(!showSettings)} className="p-2 bg-white rounded-full shadow-sm">
          <Settings className="w-5 h-5 text-gray-600" />
        </button>
      </div>

      <div className="max-w-xl mx-auto space-y-6">
        {/* Settings Modal/Area */}
        {showSettings && (
          <div className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 space-y-4">
            <h2 className="font-semibold text-gray-700">Settings</h2>
            <input 
              type="text"
              placeholder="Backend URL (e.g. http://localhost:8000)"
              className="w-full p-2 border rounded-lg text-sm"
              value={config.backendUrl}
              onChange={e => setConfig({...config, backendUrl: e.target.value})}
            />
            <input 
              type="text"
              placeholder="Google Spreadsheet URL"
              className="w-full p-2 border rounded-lg text-sm"
              value={config.sheetUrl}
              onChange={e => setConfig({...config, sheetUrl: e.target.value})}
            />
            <button 
              onClick={() => saveConfig(config)}
              className="w-full bg-gray-800 text-white py-2 rounded-lg text-sm font-medium"
            >
              Save Configuration
            </button>
          </div>
        )}

        {/* Input Area */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
          <textarea
            className="w-full h-40 p-4 outline-none resize-none"
            placeholder="Paste a job link, WhatsApp message, or description here..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
          />
          <div className="bg-gray-50 p-3 border-t">
            <button
              onClick={handleSaveJob}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-blue-300 text-white py-3 rounded-xl font-semibold flex items-center justify-center gap-2 transition-colors"
            >
              {loading ? <RefreshCw className="w-5 h-5 animate-spin" /> : <Save className="w-5 h-5" />}
              {loading ? 'Extracting & Saving...' : 'Extract & Save'}
            </button>
          </div>
        </div>

        {/* Recent Jobs */}
        <div className="space-y-3">
          <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wider ml-1">Recent Saved</h2>
          {jobs.map((job, idx) => (
            <div key={idx} className="bg-white p-4 rounded-xl shadow-sm border border-gray-100 flex justify-between items-start gap-4">
              <div className="overflow-hidden">
                <h3 className="font-semibold text-gray-800 truncate">{job.Role || job.role || 'Unknown Role'}</h3>
                <p className="text-sm text-gray-500 truncate">{job.Company || job.company || 'Unknown Company'}</p>
                <div className="flex gap-2 mt-2">
                  <span className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-md">{job.Status || job.status || 'Saved'}</span>
                  {job.Deadline && <span className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded-md">Due: {job.Deadline}</span>}
                </div>
              </div>
              {(job['Job Link'] || job.jobLink) && (
                <a 
                  href={job['Job Link'] || job.jobLink} 
                  target="_blank" 
                  rel="noreferrer"
                  className="p-2 text-gray-400 hover:text-blue-600 bg-gray-50 rounded-lg"
                >
                  <ExternalLink className="w-5 h-5" />
                </a>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}