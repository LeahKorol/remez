import os
import pickle
import pandas as pd
from pipeline.utils import read_demo_data, read_therapy_data, QuestionConfig

def mark_data(
    dir_raw_data,
    dir_config,
    dir_marked_data,
):
    """
    מכין את הנתונים המסומנים לכל קונפיגורציה ושומר כ-PKL
    """
    os.makedirs(dir_marked_data, exist_ok=True)

    # קריאת נתוני דמוגרפיה ותרופות
    fn_demo = os.path.join(dir_raw_data, "demo.csv")
    fn_therapy = os.path.join(dir_raw_data, "therapy.csv")

    df_demo = read_demo_data(fn_demo)
    df_therapy = read_therapy_data(fn_therapy)

    # חיבור דמוגרפיה ותרופות לפי caseid
    df_all = pd.merge(df_demo, df_therapy, on="caseid", how="left")

    # קונפיגורציות
    configs = QuestionConfig.load_config_items(dir_config)

    for config in configs:
        df_marked = df_all.copy()
        # יצירת עמודות חשיפה ותגובה
        df_marked[f"exposed {config.name}"] = df_marked.apply(
            lambda x: any(drug in str(x) for drug in config.drugs), axis=1
        )
        df_marked[f"reacted {config.name}"] = df_marked.apply(
            lambda x: any(rxn in str(x) for rxn in config.reactions), axis=1
        )

        # שמירה
        fn_out = os.path.join(dir_marked_data, f"{config.name}.pkl")
        with open(fn_out, "wb") as f:
            pickle.dump(df_marked, f)
        print(f"Saved marked data for {config.name} -> {fn_out}")


if __name__ == "__main__":
    import defopt
    defopt.run(mark_data)
