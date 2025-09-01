<<<<<<< HEAD
---
license: cc-by-sa-4.0
language:
- en
- fr
- de
- it
- nl
- ru
- he
task_categories:
- token-classification
pretty_name: Ingredient List Detection
size_categories:
- 1K<n<10K
---

This dataset is used to train a multilingual ingredient list detection model. The goal is to automate the extraction of ingredient lists from food packaging images. See [this issue](https://github.com/openfoodfacts/openfoodfacts-ai/issues/242) for a broader context about ingredient list extraction.

## Dataset generation

Raw unannotated texts are OCR results obtained with Google Cloud Vision. It only contains images marked as ingredient image on Open Food Facts.
The dataset was generated using ChatGPT-3.5: we asked ChatGPT to extract ingredient using the following prompt:

Prompt:
```
Extract ingredient lists from the following texts. The ingredient list should start with the first ingredient and end with the last ingredient. It should not include allergy, label or origin information.
The output format must be a single JSON list containing one element per ingredient list. If there are ingredients in several languages, the output JSON list should contain as many elements as detected languages. Each element should have two fields:
- a "text" field containing the detected ingredient list. The text should be a substring of the original text, you must not alter the original text.
- a  "lang" field containing the detected language of the ingredient list.
Don't output anything else than the expected JSON list.
```

System prompt:
```
You are ChatGPT, a large language model trained by OpenAI. Only generate responses in JSON format. The output JSON must be minified.
```

A first cleaning step was performed automatically, we removed responses with:
- invalid JSON
- JSON with missing fields
- JSON where the detected ingredient list is not a substring of the original text

A first NER model was trained on this dataset. The model prediction errors on this dataset were inspected, which allowed us to spot the different kind of annotation errors made by ChatGPT. Then, using a semi-automatic approach, we manually corrected samples that were likely to have the error spotted during the inspection phase. For example, we noticed that the prefix "Ingredients:" was sometimes included in the ingredient text span. We looked for every sample where "Ingredients" (and translations in other languages) was part of the ingredient text, and corrected these samples manually. This approach allowed us to focus on problematic samples, instead of having to check the full train set.

These detection rules were mostly implemented using regex. The cleaning script with all rules [can be found here](https://github.com/openfoodfacts/openfoodfacts-ai/blob/149447bdbcd19cb7c15127405d9112bc9bfe3685/ingredient_extraction/clean_dataset.py#L23). 

Once the detected errors were fixed using this approach, a new dataset alpha version was released, and we trained the model on this new dataset.
Dataset was split between train (90%) and test (10%) sets. Train and test splits were kept consistent at each alpha release. Only the test dataset was fully reviewed and corrected manually.

We tokenized the text using huggingface pre-tokenizer with the `[WhitespaceSplit(), Punctuation()]` sequence. The dataset generation script [can be found here](https://github.com/openfoodfacts/openfoodfacts-ai/blob/149447bdbcd19cb7c15127405d9112bc9bfe3685/ingredient_extraction/generate_dataset.py).

This dataset is exactly the same as `ingredient-detection-alpha-v6` used during model trainings.

## Annotation guidelines

Annotations guidelines were updated continuously during dataset refinement and model trainings, but here are the final guidelines:

1. ingredient lists in all languages must be annotated.
2. ingredients list should start with the first ingredient, without `ingredient` prefix ("Ingredients:", "Zutaten", "Ingrédients: ") or `language` prefix ("EN:", "FR - ",...)
3. ingredient list containing single ingredients without any `ingredient` or `language` prefix should not be annotated. Otherwise, it's very difficult to know whether the mention is the ingredient list or just a random mention of an ingredient on the packaging.
4. We don't include most extra information (allergen, origin, trace) at the end of the ingredient list. We now include organic mentions (as of v1.1 of the dataset). Another exception is when the extra information is in bracket after the ingredient. This rule is in place to make it easier for the detector to know what is an ingredient list and what is not.

## Dataset schema

The dataset is made of 2 JSONL files:

- `ingredient_detection_dataset_train.jsonl.gz`: train split, 5065 samples
- `ingredient_detection_dataset_test.jsonl.gz`: test split, 556 samples

Each sample has the following fields:

- `text`: the original text obtained from OCR result
- `marked_text`: the text with ingredient spans delimited by `<b>` and `</b>`
- `tokens`: tokens obtained with pre-tokenization
- `ner_tags`: tag ID associated with each token: 0 for `O`, 1 for `B-ING` and 2 for `I-ING` (BIO schema)
- `offsets`: a list containing character start and end offsets of ingredients spans
- `meta`: a dict containing additional meta-data about the sample:
    - `barcode`: the product barcode of the image that was used
    - `image_id`: unique digit identifier of the image for the product
    - `url`: image URL from which the text was extracted

## Versions

### v1.1

New version of the dataset with the following modifications:

- included “*organic”/”*issu de l’agriculture biologique” suffixes as part of the ingredient list. This suffix was added manually as a postprocessing step and it did not make much sense not to include it. This was only included if the mention was just after the ingredient list (if allergen info was in between it was not included).
- Some other annotation errors were fixed as well.

### v1.0

First version of the dataset
=======
---
license: cc-by-sa-4.0
language:
- en
- fr
- de
- it
- nl
- ru
- he
task_categories:
- token-classification
pretty_name: Ingredient List Detection
size_categories:
- 1K<n<10K
---

This dataset is used to train a multilingual ingredient list detection model. The goal is to automate the extraction of ingredient lists from food packaging images. See [this issue](https://github.com/openfoodfacts/openfoodfacts-ai/issues/242) for a broader context about ingredient list extraction.

## Dataset generation

Raw unannotated texts are OCR results obtained with Google Cloud Vision. It only contains images marked as ingredient image on Open Food Facts.
The dataset was generated using ChatGPT-3.5: we asked ChatGPT to extract ingredient using the following prompt:

Prompt:
```
Extract ingredient lists from the following texts. The ingredient list should start with the first ingredient and end with the last ingredient. It should not include allergy, label or origin information.
The output format must be a single JSON list containing one element per ingredient list. If there are ingredients in several languages, the output JSON list should contain as many elements as detected languages. Each element should have two fields:
- a "text" field containing the detected ingredient list. The text should be a substring of the original text, you must not alter the original text.
- a  "lang" field containing the detected language of the ingredient list.
Don't output anything else than the expected JSON list.
```

System prompt:
```
You are ChatGPT, a large language model trained by OpenAI. Only generate responses in JSON format. The output JSON must be minified.
```

A first cleaning step was performed automatically, we removed responses with:
- invalid JSON
- JSON with missing fields
- JSON where the detected ingredient list is not a substring of the original text

A first NER model was trained on this dataset. The model prediction errors on this dataset were inspected, which allowed us to spot the different kind of annotation errors made by ChatGPT. Then, using a semi-automatic approach, we manually corrected samples that were likely to have the error spotted during the inspection phase. For example, we noticed that the prefix "Ingredients:" was sometimes included in the ingredient text span. We looked for every sample where "Ingredients" (and translations in other languages) was part of the ingredient text, and corrected these samples manually. This approach allowed us to focus on problematic samples, instead of having to check the full train set.

These detection rules were mostly implemented using regex. The cleaning script with all rules [can be found here](https://github.com/openfoodfacts/openfoodfacts-ai/blob/149447bdbcd19cb7c15127405d9112bc9bfe3685/ingredient_extraction/clean_dataset.py#L23). 

Once the detected errors were fixed using this approach, a new dataset alpha version was released, and we trained the model on this new dataset.
Dataset was split between train (90%) and test (10%) sets. Train and test splits were kept consistent at each alpha release. Only the test dataset was fully reviewed and corrected manually.

We tokenized the text using huggingface pre-tokenizer with the `[WhitespaceSplit(), Punctuation()]` sequence. The dataset generation script [can be found here](https://github.com/openfoodfacts/openfoodfacts-ai/blob/149447bdbcd19cb7c15127405d9112bc9bfe3685/ingredient_extraction/generate_dataset.py).

This dataset is exactly the same as `ingredient-detection-alpha-v6` used during model trainings.

## Annotation guidelines

Annotations guidelines were updated continuously during dataset refinement and model trainings, but here are the final guidelines:

1. ingredient lists in all languages must be annotated.
2. ingredients list should start with the first ingredient, without `ingredient` prefix ("Ingredients:", "Zutaten", "Ingrédients: ") or `language` prefix ("EN:", "FR - ",...)
3. ingredient list containing single ingredients without any `ingredient` or `language` prefix should not be annotated. Otherwise, it's very difficult to know whether the mention is the ingredient list or just a random mention of an ingredient on the packaging.
4. We don't include most extra information (allergen, origin, trace) at the end of the ingredient list. We now include organic mentions (as of v1.1 of the dataset). Another exception is when the extra information is in bracket after the ingredient. This rule is in place to make it easier for the detector to know what is an ingredient list and what is not.

## Dataset schema

The dataset is made of 2 JSONL files:

- `ingredient_detection_dataset_train.jsonl.gz`: train split, 5065 samples
- `ingredient_detection_dataset_test.jsonl.gz`: test split, 556 samples

Each sample has the following fields:

- `text`: the original text obtained from OCR result
- `marked_text`: the text with ingredient spans delimited by `<b>` and `</b>`
- `tokens`: tokens obtained with pre-tokenization
- `ner_tags`: tag ID associated with each token: 0 for `O`, 1 for `B-ING` and 2 for `I-ING` (BIO schema)
- `offsets`: a list containing character start and end offsets of ingredients spans
- `meta`: a dict containing additional meta-data about the sample:
    - `barcode`: the product barcode of the image that was used
    - `image_id`: unique digit identifier of the image for the product
    - `url`: image URL from which the text was extracted

## Versions

### v1.1

New version of the dataset with the following modifications:

- included “*organic”/”*issu de l’agriculture biologique” suffixes as part of the ingredient list. This suffix was added manually as a postprocessing step and it did not make much sense not to include it. This was only included if the mention was just after the ingredient list (if allergen info was in between it was not included).
- Some other annotation errors were fixed as well.

### v1.0

First version of the dataset
>>>>>>> acc5134 (Add ingredient-detection folder)
