source ~/.bash_profile

lang="fr"
#system="TildeMT"
system="linguacustodia"

#for kkk in blind_test.en-fr.CUNI_Contrastive_lemm_choices.fr blind_test.en-fr.CUNI_Contrastive_scored.fr blind_test.en-fr.CUNI_Contrastive_sf.fr blind_test.en-fr.CUNI_Contrastive_sf_choices.fr blind_test.en-fr.CUNI_Primary_lemm.fr blind_test.en-fr.CUNI_Primary_not_scored.fr
for kkk in baseline1_enfr baseline2_enfr
do
#kkk="kep_final.de"

file="outputs/${system}/${kkk}"
input=${file}.sgm
output=${file}.txt

cd /Users/antonios/Desktop/research/WMTSharedTask/terminology_evaluation

py unwrap-xml.py --input_file ${input}

echo "Unwrapped the hypothesis"

if [[ ${lang} == "de" ]]
then
	truecaser="Truecasers/opus.de-en-train.de.truecaser "
	source="gold/test.cs-${lang}.cs.sgm"
	target="gold/testset.cs-${lang}.${lang}.sgm"
	targetbleu="gold/testset.cs-${lang}.${lang}.txt"
else
	truecaser="Truecasers/opus.en-${lang}-train.${lang}.truecaser "
	source="gold/test.en-${lang}.en.sgm"
	target="gold/test.en-${lang}.${lang}.sgm"
	targetbleu="gold/test.en-${lang}.${lang}.txt"
fi

echo "The target is: ${target}"

echo $source
echo $target
echo $output
echo $truecaser


py util_preprocessor.py --language ${lang} --directory ${output} --moses_directory mosesdecoder/ --truecasing True --truecaser_model ${truecaser}

echo "Finished preprocessing"

perl mosesdecoder/scripts/ems/support/wrap-xml.perl ${lang} ${source} ${system} < "${file}.txt.truecased" > "${file}.truecased.sgm"

echo "Wrapped truecased and tokenized file."
echo "Starting evaluation"

py evaluate_term_wmt.py --language ${lang} --hypothesis ${file}.truecased.sgm --source ${source} --target_reference ${target} --log ${file}.eval.log

echo "Done"

done