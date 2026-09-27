"""Portable human review guide attached to a specific trained run."""
from core import text_report


def model_review_card(run):
    return '\n'.join([
        'SignalReady model review card',
        'Purpose: help an engineer review a local classification prototype.',
        'Review status: human review required. This card is not deployment approval.',
        '',
        text_report(run),
        '',
        'Before using these results',
        '1. Confirm the source data may be used and that sensor units match the approved inputs.',
        '2. Review missed failures and false alarms with the person responsible for the equipment.',
        '3. Run the app completion checks for this run and retain their separate evidence. This card does not certify that those checks passed.',
        '4. Test later time periods and different machines using suitable real equipment data before claiming factory performance.',
        '5. Check incoming readings for unfamiliar ranges. A range check cannot establish safety or detect every distribution change.',
        '6. Define the human response to warnings. Predictions are not repair instructions.',
        '7. Keep this app on one trusted local computer. Protect saved models and downloads. Load only trusted local model files.',
        '',
        'What this card contains',
        'Run identity and aggregate results only. It includes the source label supplied during training but no raw readings or executable model.',
        'Treat this card as sensitive if its source label or aggregate results are confidential.',
    ])
