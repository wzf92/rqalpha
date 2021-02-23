from enum import Enum
import os
import copy
import csv 


class PositionState(Enum):
    NONE = 0
    HOLDING_LONG = 1
    HOLDING_SHORT = 2


class Operation(Enum):
    NONE = 0
    OPEN_LONG = 1
    OPEN_SHORT = 2
    CLOSE_LONG = 3
    CLOSE_SHORT = 4


class SplitTradeSide():
    def __init__(self):
        pass

    def split_side(self, input_file_name):
#        side_index = -1
#        position_effect_index = -1
#        last_quantity_index = -1
#        last_price_index = -1
#        transaction_cost_index = -1
        dir_name = os.path.dirname(input_file_name)
        file_name = os.path.basename(input_file_name)
        file_name_v = file_name.split('.')
        origin_prefix = copy.deepcopy(file_name_v[-2])
        file_name_v[-2] = origin_prefix + '_long'
        output_file_name_1 = os.path.join(dir_name, '.'.join(file_name_v))
        file_name_v[-2] = origin_prefix + '_short'
        output_file_name_2 = os.path.join(dir_name, '.'.join(file_name_v))

        with open(input_file_name, 'r') as in_f, open(output_file_name_1, 'w') as out1_f, open(output_file_name_2, 'w') as out2_f:
            reader = csv.reader(in_f)
            header_row = next(reader)
            for i in range(len(header_row)):
                if header_row[i] == 'side':
                    side_index = i
                elif header_row[i] == 'position_effect':
                    position_effect_index = i
                elif header_row[i] == 'last_quantity':
                    last_quantity_index = i
                elif header_row[i] == 'last_price':
                    last_price_index = i
                elif header_row[i] == 'transaction_cost':
                    transaction_cost_index = i

            state = PositionState.NONE
            result_lines_1 = []
            result_lines_2 = []
            result_lines_1.append(header_row + ['single_profit', 'accumulate_profit'])
            result_lines_2.append(header_row + ['single_profit', 'accumulate_profit'])
            for line in reader:
                buy_or_sell = line[side_index]
                open_or_close = line[position_effect_index].split('_')[0]
                if buy_or_sell == 'BUY' and open_or_close == 'OPEN':
                    operation = Operation.OPEN_LONG
                elif buy_or_sell == 'BUY' and open_or_close == 'CLOSE':
                    operation = Operation.CLOSE_SHORT
                elif buy_or_sell == 'SELL' and open_or_close == 'OPEN':
                    operation = Operation.OPEN_SHORT
                elif buy_or_sell == 'SELL' and open_or_close == 'CLOSE':
                    operation = Operation.CLOSE_LONG
                else:
                    assert False, 'unknown operation: %s, %s' % (line[side_index], line[position_effect_index])

                if state == PositionState.NONE and operation == Operation.OPEN_LONG:
                    state = PositionState.HOLDING_LONG
                elif state == PositionState.NONE and operation == Operation.OPEN_SHORT:
                    state = PositionState.HOLDING_SHORT
                elif state == PositionState.HOLDING_LONG and operation == Operation.CLOSE_LONG:
                    state = PositionState.NONE
                elif state == PositionState.HOLDING_SHORT and operation == Operation.CLOSE_SHORT:
                    state = PositionState.NONE
                else:
                    assert false, 'invalid operation. current state is "%d", operation is "%d"' % (state, operation)

                if operation in [Operation.OPEN_LONG, Operation.CLOSE_LONG]:
                    result_lines_1.append(line)
                elif operation in [Operation.OPEN_SHORT, Operation.CLOSE_SHORT]:
                    result_lines_2.append(line)

            writer = csv.writer(out1_f)
            writer.writerows(result_lines_1)
            writer = csv.writer(out2_f)
            writer.writerows(result_lines_2)



if __name__ == '__main__':
    split_trade_side = SplitTradeSide()
    split_trade_side.split_side('trades.csv', 'trades_long.csv', 'trades_short.csv')

