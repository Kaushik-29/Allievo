import React, { useState } from "react";
import { Card } from "../components/shared/Card";
import { Button } from "../components/shared/Button";
import { 
  MessageSquare, 
  Phone, 
  ChevronDown, 
  ChevronUp, 
  Send,
  LifeBuoy
} from "lucide-react";

export default function Support() {
  const [openFaq, setOpenFaq] = useState<number | null>(0);

  const faqs = [
    {
      q: "What is DAE and how is it calculated?",
      a: "DAE stands for Daily Average Earnings. We sync your last 30 days of earnings from Zomato/Swiggy to find your typical daily income. Your payout is then based on (DAE / 8) for every hour of disruption verified."
    },
    {
      q: "Why was my claim partially paid?",
      a: "Partial payouts (usually 60%) happen when GPS or platform data is intermittent. We release the first 60% immediately and the remaining 40% after manual verification (usually within 24 hours)."
    },
    {
      q: "How do I switch my insurance tier?",
      a: "You can change your tier anytime from the Policy page. The new tier and premium will apply from the next Monday at 00:00 IST."
    },
    {
      q: "My zone is flooded but no alert is showing?",
      a: "Alerts are triggered by official IMD rainfall data (65mm/hr+) or significant order drops. If you feel an alert is missing, please Raise a Ticket below."
    }
  ];

  return (
    <div className="space-y-6 animate-fade-in pb-20">
      <header className="px-2">
        <h2 className="text-2xl font-black text-gray-900 leading-tight">Support</h2>
        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mt-1">24/7 Protection Assistance</p>
      </header>

      {/* Quick Contact Grid */}
      <div className="grid grid-cols-2 gap-4">
         <ContactCard 
          icon={<Phone className="text-primary-600" />} 
          label="Call Support" 
          value="1800-ALLIEVO" 
          className="bg-primary-50 border-primary-100"
         />
         <ContactCard 
          icon={<MessageSquare className="text-emerald-600" />} 
          label="WhatsApp" 
          value="+91 91234 56789" 
          className="bg-emerald-50 border-emerald-100"
         />
      </div>

      {/* FAQs */}
      <section>
        <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 px-2">Common Questions</h4>
        <Card className="p-0 overflow-hidden divide-y divide-gray-50">
           {faqs.map((faq, i) => (
              <div key={i} className="group">
                 <button 
                  onClick={() => setOpenFaq(openFaq === i ? null : i)}
                  className="w-full p-5 flex items-center justify-between text-left hover:bg-gray-50 transition-colors"
                 >
                    <span className="font-bold text-sm text-gray-800 leading-tight">{faq.q}</span>
                    {openFaq === i ? <ChevronUp className="w-4 h-4 text-primary-600" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
                 </button>
                 {openFaq === i && (
                    <div className="px-5 pb-6 text-xs font-medium text-gray-500 leading-relaxed bg-gray-50/50 animate-slide-up">
                       {faq.a}
                    </div>
                 )}
              </div>
           ))}
        </Card>
      </section>

      {/* Raise a Ticket */}
      <section>
        <h4 className="text-xs font-black text-gray-400 uppercase tracking-widest mb-4 px-2">Raise a Ticket</h4>
        <Card className="p-8">
           <div className="flex items-center gap-4 mb-6">
              <div className="p-3 bg-amber-50 rounded-2xl text-amber-600">
                 <LifeBuoy className="w-6 h-6" />
              </div>
              <div>
                 <h4 className="font-bold text-gray-900 leading-none mb-1">Still need help?</h4>
                 <p className="text-[10px] font-bold text-gray-400 uppercase tracking-widest">Our team replies in 15 mins</p>
              </div>
           </div>
           
           <div className="space-y-4">
              <textarea 
                className="w-full h-32 p-5 rounded-[2rem] border-2 border-gray-50 font-medium text-sm focus:border-primary-600 underline-none resize-none placeholder:text-gray-200 bg-gray-50/30"
                placeholder="Describe your issue or concern here..."
              />
              <Button type="button" className="w-full py-5 text-lg shadow-xl shadow-primary-200">
                 SEND MESSAGE <Send className="ml-2 w-5 h-5 stroke-[2.5]" />
              </Button>
           </div>
        </Card>
      </section>

      <footer className="text-center pt-4 opacity-40">
         <p className="text-[10px] font-black uppercase tracking-[0.3em]">Allievo IRDAI Reg #88921</p>
      </footer>
    </div>
  );
}

function ContactCard({ icon, label, value, className }: any) {
  return (
    <Card variant="outline" className={`p-4 text-center cursor-pointer hover:border-primary-600 transition-all active:scale-[0.98] ${className}`}>
       <div className="inline-block p-2 bg-white rounded-xl shadow-sm mb-3">
          {React.cloneElement(icon, { className: "w-5 h-5" })}
       </div>
       <p className="text-[8px] font-black text-gray-400 uppercase tracking-widest mb-1">{label}</p>
       <p className="text-xs font-black text-gray-900">{value}</p>
    </Card>
  );
}
