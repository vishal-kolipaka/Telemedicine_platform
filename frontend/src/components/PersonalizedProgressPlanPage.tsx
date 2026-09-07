import React, { useState, useEffect } from 'react';
import type { HealthAssessmentResponse } from '../types/reader';
import type { ProgressPlanRecord } from '../types/progress_plan';
import {
  generateProgressPlan,
  getProgressPlan,
  toggleProgressPlanTask,
  resetProgressPlan,
  downloadProgressPlanPdf,
} from '../services/api';
import {
  Sparkles,
  ArrowLeft,
  Download,
  RotateCcw,
  CheckCircle2,
  Lock,
  Unlock,
  Calendar,
  User,
  Activity,
  Apple,
  Scale,
  Clock,
  ShieldCheck,
  Check,
  AlertCircle,
} from 'lucide-react';

interface Props {
  assessment: HealthAssessmentResponse;
  initialDuration?: '1_week' | '1_month' | '3_months';
  onBack: () => void;
  onReset?: () => void;
}

export const PersonalizedProgressPlanPage: React.FC<Props> = ({
  assessment,
  initialDuration = '1_week',
  onBack,
}) => {
  const [duration, setDuration] = useState<'1_week' | '1_month' | '3_months'>(initialDuration);
  const [planRecord, setPlanRecord] = useState<ProgressPlanRecord | null>(null);
  const [selectedDayNumber, setSelectedDayNumber] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloadingPdf, setDownloadingPdf] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    patient_id,
    patient_name,
    patient_age,
    patient_gender,
    assessment_timestamp,
  } = assessment;

  const formattedDate = new Date(assessment_timestamp).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });

  // Load or generate plan for the active duration
  useEffect(() => {
    let isMounted = true;
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });

    const fetchOrCreatePlan = async () => {
      setLoading(true);
      setErrorMsg(null);

      // Check if we have a stored plan_id in localStorage for this patient + duration
      const storageKey = `telemed_plan_${patient_id}_${duration}`;
      const savedPlanId = localStorage.getItem(storageKey);

      try {
        let record: ProgressPlanRecord | null = null;
        if (savedPlanId) {
          try {
            record = await getProgressPlan(savedPlanId);
          } catch (fetchErr) {
            // If expired or not on server, generate fresh
            record = null;
          }
        }

        if (!record) {
          record = await generateProgressPlan({
            patient_id,
            patient_name: patient_name || undefined,
            patient_age: patient_age || undefined,
            patient_gender: patient_gender || undefined,
            duration,
            health_plan: assessment.health_plan || {},
          });
          localStorage.setItem(storageKey, record.plan_id);
        }

        if (isMounted) {
          setPlanRecord(record);
          setSelectedDayNumber(record.current_day || 1);
          setLoading(false);
        }
      } catch (err: any) {
        if (isMounted) {
          setErrorMsg(err.message || 'Failed to initialize progress plan.');
          setLoading(false);
        }
      }
    };

    fetchOrCreatePlan();

    return () => {
      isMounted = false;
    };
  }, [duration, patient_id, assessment.health_plan, patient_name, patient_age, patient_gender]);

  // Handle task check toggle
  const handleToggleTask = async (taskId: string, currentCompleted: boolean) => {
    if (!planRecord) return;

    try {
      const updated = await toggleProgressPlanTask(planRecord.plan_id, taskId, !currentCompleted);
      setPlanRecord(updated);
    } catch (err: any) {
      console.error('Failed to toggle task:', err);
    }
  };

  // Handle plan reset
  const handleResetProgress = async () => {
    if (!planRecord) return;
    const confirmReset = window.confirm('Are you sure you want to reset all progress back to Day 1?');
    if (!confirmReset) return;

    try {
      const resetRec = await resetProgressPlan(planRecord.plan_id);
      setPlanRecord(resetRec);
      setSelectedDayNumber(1);
    } catch (err: any) {
      console.error('Failed to reset progress:', err);
    }
  };

  // Handle PDF Download
  const handleDownloadPdf = async () => {
    if (!planRecord) return;
    setDownloadingPdf(true);
    try {
      const filename = `health_progress_plan_${duration}_${patient_id}.pdf`;
      await downloadProgressPlanPdf(planRecord.plan_id, filename);
    } catch (err: any) {
      alert('Failed to download PDF report. Please try again.');
    } finally {
      setDownloadingPdf(false);
    }
  };

  // Icon selector helper
  const getPillarIcon = (category: string) => {
    const c = category.toLowerCase();
    if (c.includes('activity') || c.includes('physical') || c.includes('move')) {
      return <Activity className="w-5 h-5 text-emerald-600" />;
    }
    if (c.includes('diet') || c.includes('nutrition') || c.includes('food') || c.includes('fibre')) {
      return <Apple className="w-5 h-5 text-sky-600" />;
    }
    if (c.includes('weight') || c.includes('caloric')) {
      return <Scale className="w-5 h-5 text-indigo-600" />;
    }
    return <Clock className="w-5 h-5 text-amber-600" />;
  };

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-12 text-center space-y-4">
        <div className="w-12 h-12 border-4 border-sky-600 border-t-transparent rounded-full animate-spin mx-auto" />
        <p className="text-sm font-bold text-slate-700">Personalizing your {duration.replace('_', ' ')} progress plan...</p>
      </div>
    );
  }

  if (errorMsg || !planRecord) {
    return (
      <div className="max-w-5xl mx-auto py-8 space-y-6">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-white hover:bg-slate-100 text-slate-800 text-sm font-bold rounded-2xl border border-slate-200 shadow-xs cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Assessment</span>
        </button>

        <div className="bg-white rounded-3xl p-8 border border-slate-200 shadow-xl text-center space-y-4">
          <AlertCircle className="w-10 h-10 text-rose-500 mx-auto" />
          <h2 className="text-xl font-extrabold text-slate-900">Unable to Load Progress Plan</h2>
          <p className="text-sm text-slate-600 max-w-md mx-auto">{errorMsg || 'Please try again.'}</p>
          <button
            type="button"
            onClick={onBack}
            className="px-6 py-2.5 bg-sky-600 text-white font-bold text-xs rounded-xl hover:bg-sky-700"
          >
            Return to Assessment
          </button>
        </div>
      </div>
    );
  }

  const { plan_data, completed_tasks, completed_days, current_day, overall_progress } = planRecord;
  const completedTaskSet = new Set(completed_tasks || []);
  const completedDaySet = new Set(completed_days || []);
  const allDays = plan_data.days || [];

  const selectedDay = allDays.find((d) => d.day_number === selectedDayNumber) || allDays[0];
  const isSelectedDayUnlocked = selectedDay ? (selectedDay.day_number <= current_day || selectedDay.is_unlocked) : true;
  const isSelectedDayCompleted = selectedDay ? completedDaySet.has(selectedDay.day_number) : false;

  const dayTasks = selectedDay?.tasks || [];
  const dayDoneCount = dayTasks.filter((t) => completedTaskSet.has(t.id)).length;
  const dayProgressPct = dayTasks.length > 0 ? Math.round((dayDoneCount / dayTasks.length) * 100) : 0;

  return (
    <div className="space-y-8 max-w-6xl mx-auto py-4 animate-fade-in text-slate-900">
      {/* ── TOP ACTION BAR & HEADER ────────────────────────────────────────── */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6">
          <button
            type="button"
            onClick={onBack}
            className="inline-flex items-center space-x-2 px-4 py-2.5 bg-slate-100 hover:bg-slate-200 text-slate-800 text-xs font-bold rounded-2xl transition-all cursor-pointer self-start sm:self-auto"
          >
            <ArrowLeft className="w-4 h-4 text-slate-600" />
            <span>Back to Personalized Plan</span>
          </button>

          {/* Duration Selector Tabs */}
          <div className="flex items-center bg-slate-100 p-1 rounded-2xl border border-slate-200 self-start sm:self-auto">
            <button
              type="button"
              onClick={() => setDuration('1_week')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                duration === '1_week'
                  ? 'bg-white text-sky-900 shadow-xs border border-slate-200/80'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              1 Week Plan
            </button>
            <button
              type="button"
              onClick={() => setDuration('1_month')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                duration === '1_month'
                  ? 'bg-white text-sky-900 shadow-xs border border-slate-200/80'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              1 Month Plan
            </button>
            <button
              type="button"
              onClick={() => setDuration('3_months')}
              className={`px-3.5 py-1.5 rounded-xl text-xs font-black transition-all cursor-pointer ${
                duration === '3_months'
                  ? 'bg-white text-sky-900 shadow-xs border border-slate-200/80'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              3 Months Plan
            </button>
          </div>

          {/* Right Action Buttons */}
          <div className="flex items-center space-x-2.5">
            <button
              type="button"
              onClick={handleDownloadPdf}
              disabled={downloadingPdf}
              className="flex items-center space-x-2 px-4 py-2.5 bg-sky-600 hover:bg-sky-700 text-white text-xs font-bold rounded-2xl shadow-md shadow-sky-600/20 transition-all cursor-pointer disabled:opacity-50"
            >
              <Download className="w-4 h-4" />
              <span>{downloadingPdf ? 'Generating PDF...' : 'Download My Plan PDF'}</span>
            </button>
            <button
              type="button"
              onClick={handleResetProgress}
              title="Reset progress to Day 1"
              className="p-2.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-2xl transition-colors cursor-pointer"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Hero Title & Meta */}
        <div className="space-y-3">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-extrabold border border-emerald-300">
            <Sparkles className="w-3.5 h-3.5 text-emerald-700" />
            <span>Personalized Daily Progress Tracker</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-extrabold text-slate-950 tracking-tight">
            🎯 Your {plan_data.duration_label}
          </h1>

          <p className="text-sm sm:text-base text-slate-700 max-w-3xl leading-relaxed font-medium">
            Turn your health recommendations into a simple, step-by-step daily plan. Complete today's checklist to unlock the next day and build lasting healthy habits.
          </p>

          <div className="pt-2 text-xs text-slate-500 flex flex-wrap items-center gap-3">
            <span className="flex items-center space-x-1">
              <Calendar className="w-3.5 h-3.5 text-slate-400" />
              <span>{formattedDate}</span>
            </span>
            <span>•</span>
            <span className="flex items-center space-x-1">
              <User className="w-3.5 h-3.5 text-slate-400" />
              <span>Patient ID: <strong className="font-mono text-slate-700">{patient_id}</strong></span>
            </span>
            {patient_name && (
              <>
                <span>•</span>
                <span>Name: <strong className="text-slate-800">{patient_name}</strong></span>
              </>
            )}
            {patient_age && (
              <>
                <span>•</span>
                <span>Age: <strong className="text-slate-800">{patient_age} yrs</strong></span>
              </>
            )}
            {patient_gender && (
              <>
                <span>•</span>
                <span>Gender: <strong className="text-slate-800">{patient_gender}</strong></span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* ── OVERALL PROGRESS & DURATION TIMELINE ────────────────────────────── */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6">
        {/* Overall Completion Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">
              OVERALL PLAN PROGRESS
            </span>
            <div className="text-2xl sm:text-3xl font-black text-slate-950 mt-0.5 flex items-baseline space-x-2">
              <span>{overall_progress}%</span>
              <span className="text-xs font-bold text-slate-500">
                ({completedTaskSet.size} of {plan_data.total_tasks} tasks completed • {completedDaySet.size} of {plan_data.total_days} days done)
              </span>
            </div>
          </div>

          <div className="w-full sm:w-64">
            <div className="h-3 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
              <div
                className="h-full bg-gradient-to-r from-emerald-500 to-teal-500 transition-all duration-500 rounded-full"
                style={{ width: `${Math.max(2, overall_progress)}%` }}
              />
            </div>
          </div>
        </div>

        {/* ── 3 MONTHS: PHASE SELECTOR ──────────────────────────────────────── */}
        {duration === '3_months' && plan_data.phases && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3.5 pt-2">
            {plan_data.phases.map((phase) => {
              const isCurrentPhase = selectedDay?.phase_number === phase.phase_number;
              return (
                <div
                  key={phase.phase_number}
                  className={`p-4 rounded-2xl border-2 transition-all ${
                    isCurrentPhase
                      ? 'bg-sky-50/80 border-sky-500 text-sky-950 shadow-xs'
                      : 'bg-slate-50 border-slate-200 text-slate-700'
                  }`}
                >
                  <div className="text-[11px] font-black uppercase text-sky-700 tracking-wider">
                    {phase.weeks_label || `Phase ${phase.phase_number}`}
                  </div>
                  <h4 className="font-extrabold text-sm text-slate-900 mt-0.5">{phase.title}</h4>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{phase.subtitle}</p>
                </div>
              );
            })}
          </div>
        )}

        {/* ── 1 MONTH: WEEK SELECTOR ────────────────────────────────────────── */}
        {duration === '1_month' && plan_data.weeks && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
            {plan_data.weeks.map((w) => {
              const isSelectedWeek = selectedDay?.week_number === w.week_number;
              return (
                <div
                  key={w.week_number}
                  className={`p-3.5 rounded-2xl border-2 transition-all ${
                    isSelectedWeek
                      ? 'bg-sky-50/80 border-sky-500 text-sky-950 shadow-xs'
                      : 'bg-slate-50 border-slate-200 text-slate-700'
                  }`}
                >
                  <div className="text-[11px] font-black text-sky-700 uppercase">Week {w.week_number}</div>
                  <div className="text-xs font-extrabold text-slate-900 mt-0.5 line-clamp-1">{w.title.split(': ')[1] || w.title}</div>
                </div>
              );
            })}
          </div>
        )}

        {/* ── DAY-BY-DAY NAVIGATION STRIP ────────────────────────────────────── */}
        <div className="space-y-2 pt-2 border-t border-slate-100">
          <div className="flex items-center justify-between text-xs font-bold text-slate-600">
            <span>SELECT DAY TO VIEW CHECKLIST</span>
            <span className="text-[11px] font-semibold text-slate-500">
              Current Active: Day {current_day}
            </span>
          </div>

          <div className="flex items-center gap-2 overflow-x-auto pb-2 pt-1 scrollbar-thin">
            {allDays.map((d) => {
              const isSelected = d.day_number === selectedDayNumber;
              const isDone = completedDaySet.has(d.day_number);
              const isUnlocked = d.day_number <= current_day || d.is_unlocked;

              let btnStyle = 'bg-slate-100 text-slate-400 border-slate-200 cursor-not-allowed opacity-75';
              if (isDone) {
                btnStyle = isSelected
                  ? 'bg-emerald-600 text-white border-emerald-700 shadow-md ring-2 ring-emerald-400/40'
                  : 'bg-emerald-50 text-emerald-900 border-emerald-300 hover:bg-emerald-100';
              } else if (isUnlocked) {
                btnStyle = isSelected
                  ? 'bg-sky-600 text-white border-sky-700 shadow-md ring-2 ring-sky-400/40'
                  : 'bg-white text-slate-800 border-slate-300 hover:border-sky-400 hover:bg-sky-50/50';
              }

              return (
                <button
                  key={d.day_number}
                  type="button"
                  onClick={() => setSelectedDayNumber(d.day_number)}
                  className={`flex flex-col items-center justify-center min-w-[76px] py-2.5 px-3 rounded-2xl border font-bold text-xs transition-all shrink-0 cursor-pointer ${btnStyle}`}
                >
                  <span className="text-[10px] uppercase font-mono tracking-tighter opacity-80">
                    DAY {d.day_number}
                  </span>
                  <div className="mt-1">
                    {isDone ? (
                      <CheckCircle2 className="w-4 h-4 text-emerald-500 inline-block fill-emerald-100" />
                    ) : isUnlocked ? (
                      <Unlock className="w-4 h-4 text-sky-500 inline-block" />
                    ) : (
                      <Lock className="w-4 h-4 text-slate-400 inline-block" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── SELECTED DAY FOCUS & TASK CHECKLIST ──────────────────────────────── */}
      <div className="bg-white p-6 sm:p-8 rounded-3xl border border-slate-200 shadow-xl shadow-sky-500/5 space-y-6">
        {/* Selected Day Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-slate-100">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="text-xs font-black uppercase tracking-wider text-sky-700 bg-sky-50 px-2.5 py-0.5 rounded-full border border-sky-200">
                DAY {selectedDay?.day_number}
              </span>
              {isSelectedDayCompleted && (
                <span className="inline-flex items-center space-x-1 text-xs font-black text-emerald-800 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-300">
                  <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  <span>COMPLETED ✓</span>
                </span>
              )}
              {!isSelectedDayUnlocked && (
                <span className="inline-flex items-center space-x-1 text-xs font-bold text-slate-600 bg-slate-100 px-2.5 py-0.5 rounded-full border border-slate-300">
                  <Lock className="w-3.5 h-3.5 text-slate-500" />
                  <span>LOCKED</span>
                </span>
              )}
            </div>

            <h2 className="text-xl sm:text-2xl font-black text-slate-950 tracking-tight">
              {selectedDay?.focus_theme || `Day ${selectedDay?.day_number} Focus`}
            </h2>
          </div>

          {/* Day Progress Ring / Counter */}
          <div className="flex items-center space-x-3 bg-slate-50 p-3 rounded-2xl border border-slate-200 self-start sm:self-auto">
            <div>
              <div className="text-[10px] font-bold text-slate-500 uppercase">DAY PROGRESS</div>
              <div className="text-sm font-black text-slate-900">
                {dayDoneCount} of {dayTasks.length} Tasks ({dayProgressPct}%)
              </div>
            </div>
            <div className="w-12 h-1.5 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-emerald-500 rounded-full transition-all duration-300"
                style={{ width: `${dayProgressPct}%` }}
              />
            </div>
          </div>
        </div>

        {/* Celebratory Banner when Day is Completed */}
        {isSelectedDayCompleted && (
          <div className="p-4 rounded-2xl bg-emerald-50 border-2 border-emerald-300 flex items-center space-x-3 text-emerald-950">
            <div className="w-8 h-8 rounded-full bg-emerald-600 text-white flex items-center justify-center font-bold shrink-0">
              ✓
            </div>
            <div>
              <strong className="block text-sm font-extrabold">Day {selectedDay?.day_number} Complete!</strong>
              <p className="text-xs text-emerald-900">
                Great job completing all required tasks for today. Day {selectedDay?.day_number + 1} is unlocked.
              </p>
            </div>
          </div>
        )}

        {/* Locked Day Warning */}
        {!isSelectedDayUnlocked && (
          <div className="p-5 rounded-2xl bg-slate-100 border border-slate-300 text-slate-700 flex items-start space-x-3">
            <Lock className="w-5 h-5 text-slate-500 shrink-0 mt-0.5" />
            <div className="space-y-1">
              <strong className="text-sm font-bold text-slate-900">Day {selectedDay?.day_number} is currently locked</strong>
              <p className="text-xs text-slate-600 leading-relaxed">
                To build steady, sustainable habits, complete all required tasks in Day {selectedDay?.day_number - 1} first.
              </p>
            </div>
          </div>
        )}

        {/* ── TASK CARDS LIST (4 to 6 Tasks) ─────────────────────────────────── */}
        <div className="space-y-4 pt-1">
          {dayTasks.map((task) => {
            const isChecked = completedTaskSet.has(task.id);

            return (
              <div
                key={task.id}
                onClick={() => {
                  if (isSelectedDayUnlocked) {
                    handleToggleTask(task.id, isChecked);
                  }
                }}
                className={`p-5 sm:p-6 rounded-3xl border-2 transition-all flex flex-col sm:flex-row sm:items-start gap-4 ${
                  isChecked
                    ? 'bg-emerald-50/40 border-emerald-300 shadow-xs'
                    : isSelectedDayUnlocked
                    ? 'bg-white border-slate-200 hover:border-sky-300 shadow-sm cursor-pointer'
                    : 'bg-slate-50 border-slate-200 opacity-60'
                }`}
              >
                {/* Large Custom Checkbox */}
                <div className="pt-0.5 shrink-0">
                  <div
                    className={`w-7 h-7 rounded-xl flex items-center justify-center border-2 transition-all ${
                      isChecked
                        ? 'bg-emerald-600 border-emerald-600 text-white shadow-xs'
                        : 'bg-white border-slate-300 hover:border-sky-500'
                    }`}
                  >
                    {isChecked && <Check className="w-4 h-4 text-white stroke-[3]" />}
                  </div>
                </div>

                {/* Task Details */}
                <div className="space-y-2.5 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <div className="p-1.5 rounded-lg bg-slate-100 border border-slate-200">
                        {getPillarIcon(task.category)}
                      </div>
                      <h3
                        className={`text-base sm:text-lg font-extrabold text-slate-950 ${
                          isChecked ? 'line-through text-slate-500' : ''
                        }`}
                      >
                        {task.title}
                      </h3>
                    </div>

                    {task.target && (
                      <span className="text-[11px] font-black text-emerald-900 bg-emerald-100 px-2.5 py-0.5 rounded-md border border-emerald-200 shrink-0">
                        🎯 {task.target}
                      </span>
                    )}
                  </div>

                  {/* Instruction */}
                  <p className="text-xs sm:text-sm text-slate-800 leading-relaxed font-normal">
                    {task.instruction}
                  </p>

                  {/* Suggested Food or Action Callout */}
                  {task.suggestion && (
                    <div className="p-3 bg-slate-50 rounded-2xl border border-slate-200/80 text-xs text-slate-700 flex items-start space-x-2">
                      <span className="font-extrabold text-slate-900 shrink-0">Suggestion:</span>
                      <span className="text-slate-800">{task.suggestion}</span>
                    </div>
                  )}

                  {/* Why Selected Connection */}
                  <div className="text-[11px] text-slate-500 flex items-center space-x-1.5 pt-1">
                    <span className="font-bold text-slate-600">Why this matters:</span>
                    <span>{task.why_selected}</span>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* ── MEDICAL ADVISORY DISCLAIMER ────────────────────────────────────── */}
      <div className="p-5 rounded-2xl bg-sky-50/70 border border-sky-200 text-xs sm:text-sm text-slate-700 flex items-start space-x-3 leading-relaxed">
        <ShieldCheck className="w-5 h-5 text-sky-700 shrink-0 mt-0.5" />
        <p>
          <strong className="text-slate-900 font-bold">Medical Advisory:</strong> This personalized progress plan is generated using verified clinical practice guidelines (CDC National DPP, WHO Physical Activity, EASL Clinical Guidance) for informational and lifestyle support. It is not a substitute for professional medical advice, diagnosis, or treatment.
        </p>
      </div>
    </div>
  );
};
