TGT_FILE = test-demo-exact.tsv test-demo-jumbled.tsv
TGT_DIR = demo-rasa

.PHONY: all
all: $(TGT_FILE) $(TGT_DIR)

.PHONY: clean
clean:
	rm -f $(TGT_FILE)
	rm -rf $(TGT_DIR)

FAQs-rasa.json: FAQs.top
	./top2rasa.py < $< > $@

demo-rasa: demo-rasa.json
	./rasatrain.py $< $@

FAQs-rasa: FAQs-rasa.json
	./rasatrain.py $< $@

test-demo-exact.tsv: demo-rasa.json
	jq -r '.rasa_nlu_data.common_examples |  map([.intent, .text] | join("\t")) | join("\n")' < $< > $@

test-demo-jumbled.tsv: test-demo-exact.tsv
	cut -f2 $< |./jumble.pl -n=4 > $@.text.tmp
	cut -f1 $< |paste - $@.text.tmp > $@
	rm -f $@.text.tmp

