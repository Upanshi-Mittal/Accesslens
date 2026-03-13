'use client';

import { Engine } from '@/lib/types';
import { useState } from 'react';
import { Search, Settings2, Sparkles, Check, ChevronDown, ChevronUp } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface AuditFormProps {
  url: string;
  setUrl: (url: string) => void;
  onStartAudit: (url: string, options: { engines: string[], enableAI: boolean }) => void;
  isLoading: boolean;
  engines?: Engine[];
}

export function AuditForm({ url, setUrl, onStartAudit, isLoading, engines }: AuditFormProps) {
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [selectedEngines, setSelectedEngines] = useState<string[]>([
    'wcag_deterministic',
    'structural_engine',
    'contrast_engine'
  ]);
  const [enableAI, setEnableAI] = useState(false);

  const handleEngineToggle = (engineName: string) => {
    setSelectedEngines(prev =>
      prev.includes(engineName)
        ? prev.filter(e => e !== engineName)
        : [...prev, engineName]
    );
  };

  return (
    <div className="w-full max-w-4xl mx-auto">
      <form
        onSubmit={(e) => {
          e.preventDefault();
          onStartAudit(url, { engines: selectedEngines, enableAI });
        }}
        className="relative group"
      >

        {/* Glow border */}
        <div className="absolute -inset-1 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-2xl blur opacity-25 group-hover:opacity-40 transition duration-700"></div>

        {/* Main card */}
        <div className="relative bg-slate-900/70 border border-slate-800 rounded-2xl backdrop-blur-xl p-3 flex flex-col md:flex-row gap-3">

          {/* Input */}
          <div className="relative flex-1">
            <div className="absolute inset-y-0 left-4 flex items-center pointer-events-none">
              <Search className="h-5 w-5 text-slate-500" />
            </div>

            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter website URL for audit..."
              className="w-full pl-12 pr-4 py-4 bg-slate-900 border border-slate-700 rounded-xl text-white placeholder:text-slate-500 focus:outline-none"
              required
              disabled={isLoading}
            />
          </div>

          {/* Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="bg-blue-600 hover:bg-blue-500 text-white font-bold px-6 py-3 rounded-xl flex items-center justify-center gap-2 min-w-[180px] transition"
          >
            {isLoading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
              >
                <Sparkles className="h-5 w-5" />
              </motion.div>
            ) : (
              <>
                <Sparkles className="h-5 w-5" />
                <span>Start Audit</span>
              </>
            )}
          </button>
        </div>

        {/* Advanced button */}
        <div className="mt-4 flex justify-center">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="flex items-center gap-2 text-sm font-medium text-slate-400 hover:text-white transition-colors py-1 px-3 rounded-full hover:bg-white/5"
          >
            <Settings2 className="h-4 w-4" />
            <span>Advanced Configuration</span>
            {showAdvanced ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
        </div>

        <AnimatePresence>
          {showAdvanced && (
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="mt-4 bg-slate-900/70 border border-slate-800 rounded-2xl p-6 overflow-hidden grid grid-cols-1 md:grid-cols-2 gap-8"
            >

              {/* Engines */}
              <div>
                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center gap-2">
                  <Check className="h-4 w-4" /> Available Engines
                </h3>

                <div className="grid grid-cols-1 gap-2">
                  {engines?.map((engine) => (
                    <label
                      key={engine.name}
                      className={`flex items-center justify-between p-3 rounded-xl border transition-all cursor-pointer ${
                        selectedEngines.includes(engine.name)
                          ? 'bg-blue-500/10 border-blue-500/50 text-white'
                          : 'bg-transparent border-slate-800 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="flex items-center gap-3">

                        <input
                          type="checkbox"
                          checked={selectedEngines.includes(engine.name)}
                          onChange={() => handleEngineToggle(engine.name)}
                          className="hidden"
                        />

                        <div
                          className={`w-5 h-5 rounded-md border flex items-center justify-center transition-colors ${
                            selectedEngines.includes(engine.name)
                              ? 'bg-blue-500 border-blue-500'
                              : 'border-slate-700'
                          }`}
                        >
                          {selectedEngines.includes(engine.name) && (
                            <Check className="h-3 w-3 text-white" />
                          )}
                        </div>

                        <span className="font-medium">
                          {engine.name}
                        </span>

                      </div>

                      <span className="text-xs opacity-50">
                        v{engine.version}
                      </span>

                    </label>
                  ))}
                </div>
              </div>

              {/* AI */}
              <div>

                <h3 className="text-sm font-bold uppercase tracking-wider text-slate-500 mb-4 flex items-center gap-2">
                  <Sparkles className="h-4 w-4" /> Intelligence Settings
                </h3>

                <div
                  className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                    enableAI
                      ? 'bg-indigo-500/10 border-indigo-500/50 text-white'
                      : 'bg-transparent border-slate-800 text-slate-400 hover:border-slate-700'
                  }`}
                  onClick={() => setEnableAI(!enableAI)}
                >

                  <div className="flex items-start gap-3">

                    <div
                      className={`mt-1 w-5 h-5 rounded-md border flex items-center justify-center transition-colors ${
                        enableAI
                          ? 'bg-indigo-500 border-indigo-500'
                          : 'border-slate-700'
                      }`}
                    >
                      {enableAI && (
                        <Check className="h-3 w-3 text-white" />
                      )}
                    </div>

                    <div>
                      <p className="font-bold flex items-center gap-2">
                        Deep AI Integration

                        {enableAI && (
                          <motion.span
                            animate={{ scale: [1, 1.2, 1] }}
                            transition={{ repeat: Infinity, duration: 2 }}
                            className="px-2 py-0.5 bg-indigo-500 text-[10px] rounded-full uppercase"
                          >
                            Active
                          </motion.span>
                        )}
                      </p>

                      <p className="text-xs text-slate-500 mt-1">
                        Utilizes LLM vision for complex structural and semantic validation
                        (Significant increase in analysis time).
                      </p>
                    </div>

                  </div>

                </div>

              </div>

            </motion.div>
          )}
        </AnimatePresence>

      </form>
    </div>
  );
}