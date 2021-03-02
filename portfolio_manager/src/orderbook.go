package main

import (
	"strconv"
	"sync"

	ws "github.com/gorilla/websocket"
	log "github.com/sirupsen/logrus"
)

type OrderBook struct {
	sync.Mutex
	Bids *Book
	Asks *Book
}

type Book struct {
	IsBids    bool
	OrderDict map[string]*Order
	BestOrder *Order
}

type Order struct {
	Next  *Order
	Prev  *Order
	Price float64
	Amnt  float64
}

func InitOrderBook(bids *[][]string, asks *[][]string) *OrderBook {
	askBook := Book{
		IsBids:    false,
		OrderDict: make(map[string]*Order),
		BestOrder: nil,
	}
	bidBook := Book{
		IsBids:    true,
		OrderDict: make(map[string]*Order),
		BestOrder: nil,
	}
	newBook := OrderBook{
		Bids: &bidBook,
		Asks: &askBook,
	}
	for _, pair := range *bids {
		price := pair[0]
		amnt := pair[1]
		bidBook.Update(price, amnt)
	}
	for _, pair := range *asks {
		price := pair[0]
		amnt := pair[1]
		askBook.Update(price, amnt)
	}

	return &newBook
}

func (book *Book) Update(price string, amnt string) {
	curOrder := book.BestOrder
	priceFl, _ := strconv.ParseFloat(price, 64)
	amntFl, _ := strconv.ParseFloat(amnt, 64)

	if book.OrderDict[price] != nil {
		if amntFl == 0.0 {
			order := book.OrderDict[price]
			if order.Prev == nil {
				book.BestOrder = order.Next
			} else {
				order.Prev.Next = order.Next
			}
			if order.Next != nil {
				order.Next.Prev = order.Prev
			}
			delete(book.OrderDict, price)

		} else {
			book.OrderDict[price].Amnt = amntFl
		}
		return
	} else if amntFl == 0.0 {
		log.Warn("Order book descrepancy (tried to remove order that did not exist). This should never happen!")
		return
	}

	if curOrder == nil {
		newOrder := Order{
			Next:  nil,
			Prev:  nil,
			Price: priceFl,
			Amnt:  amntFl,
		}
		book.BestOrder = &newOrder
		book.OrderDict[price] = &newOrder
		return
	}

	if book.IsBids {
		for curOrder.Next != nil && curOrder.Price > priceFl {
			curOrder = curOrder.Next
		}
		if curOrder.Price > priceFl {
			newOrder := Order{
				Next:  nil,
				Prev:  curOrder,
				Price: priceFl,
				Amnt:  amntFl,
			}
			curOrder.Next = &newOrder
			book.OrderDict[price] = &newOrder
		} else {
			newOrder := Order{
				Next:  curOrder,
				Prev:  curOrder.Prev,
				Price: priceFl,
				Amnt:  amntFl,
			}
			if curOrder.Prev != nil {
				curOrder.Prev.Next = &newOrder
			} else {
				book.BestOrder = &newOrder
			}
			curOrder.Prev = &newOrder
			book.OrderDict[price] = &newOrder
		}

	} else {
		for curOrder.Next != nil && curOrder.Price < priceFl {
			curOrder = curOrder.Next
		}
		if curOrder.Price < priceFl {
			newOrder := Order{
				Next:  nil,
				Prev:  curOrder,
				Price: priceFl,
				Amnt:  amntFl,
			}
			curOrder.Next = &newOrder
			book.OrderDict[price] = &newOrder
		} else {
			newOrder := Order{
				Next:  curOrder,
				Prev:  curOrder.Prev,
				Price: priceFl,
				Amnt:  amntFl,
			}
			if curOrder.Prev != nil {
				curOrder.Prev.Next = &newOrder
			} else {
				book.BestOrder = &newOrder
			}

			curOrder.Prev = &newOrder
			book.OrderDict[price] = &newOrder
		}
	}
	return
}

func ConnectToCoinbaseOrderBookSocket(symbols *[]string) (*ws.Conn, error) {
	wsConn, _, err := wsDialer.Dial("wss://ws-feed.pro.coinbase.com", nil)
	if err != nil {
		return nil, err
	}
	actual_symbols := []string{}
	for _, sym := range *symbols {
		actual_symbols = append(actual_symbols, sym+"-USD")
	}

	subscribe := CoinBaseMessage{
		Type: "subscribe",
		Channels: []MessageChannel{
			MessageChannel{
				Name:       "level2",
				ProductIds: actual_symbols,
			},
		},
	}
	log.Println(subscribe)

	if err := wsConn.WriteJSON(subscribe); err != nil {
		return nil, err
	}
	return wsConn, nil
}

func getCurrentLiquidity(isBid bool, book *Book, closePrice float64, targetSlippage float64) float64 {
	totalLiquidity := 0.0
	if isBid {

		minPrice := closePrice * (1 - targetSlippage)
		curOrder := book.BestOrder
		for curOrder != nil {
			curPrice := curOrder.Price
			if curPrice < minPrice {
				break
			} else {
				totalLiquidity += (curOrder.Amnt * curOrder.Price)
				curOrder = curOrder.Next
			}
		}
	} else {
		maxPrice := closePrice * (1 + targetSlippage)
		curOrder := book.BestOrder
		for curOrder != nil {
			curPrice := curOrder.Price
			if curPrice > maxPrice {
				break
			} else {
				totalLiquidity += (curOrder.Amnt * curOrder.Price)
				curOrder = curOrder.Next
			}
		}
	}
	return totalLiquidity
}

func (pm *PortfolioManager) UpdateLiquidity() {
	for _, coin := range *pm.Coins {
		pm.CoinDict[coin].CoinOrderBook.Lock()
		pm.CoinDict[coin].BidLiquidity.Update(getCurrentLiquidity(
			true,
			pm.CoinDict[coin].CoinOrderBook.Bids,
			pm.CandleDict[coin].Close,
			pm.TargetSlippage))

		pm.CoinDict[coin].AskLiquidity.Update(getCurrentLiquidity(
			false,
			pm.CoinDict[coin].CoinOrderBook.Asks,
			pm.CandleDict[coin].Close,
			pm.TargetSlippage))

		pm.CoinDict[coin].CoinOrderBook.Unlock()
		// log.Println(coin, pm.CoinDict[coin].BidLiquidity.GetVal(), pm.CoinDict[coin].AskLiquidity.GetVal())
	}
}
