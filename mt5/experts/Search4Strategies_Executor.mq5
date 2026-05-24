//+------------------------------------------------------------------+
//| Search4Strategies Executor                                       |
//| Reads only approved signals exported by the Python research layer |
//+------------------------------------------------------------------+
#property strict

input double RiskPercent = 1.0;
input int MaxTradesPerDay = 6;
input int MagicNumber = 4042026;
input double MinRR = 3.0;

int OnInit()
{
   Print("Search4Strategies Executor initialized. Use Python strategy export for signal authority.");
   return(INIT_SUCCEEDED);
}

void OnTick()
{
   // Production execution should be connected to exported/validated strategy signals.
   // This EA is intentionally conservative: it does not invent signals internally.
}

